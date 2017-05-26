from lxml import etree
import click
import datetime
import git
import json
import shutil
import urlparse
import os
import hashlib
import fnmatch
import requests
import zipfile
import glob
from distutils.version import LooseVersion
import mistune
import sys
from bs4 import BeautifulSoup
from bs4 import SoupStrainer
import http_request

# sys.setdefaultencoding() does not exist, here!
reload(sys)  # Reload does the trick!
sys.setdefaultencoding('UTF8')

plugins_dir = 'addons'
build_dir = 'build'
temp_dir = 'temp'
build_plugins_dir = os.path.join(build_dir)
build_temp_dir = os.path.join(build_dir, temp_dir)

config = json.load(open('.repository.json'))
plugins_info = config['plugins']
repository = config['repository']
repo_name = repository['id']
repo_url = repository['url']
repo_source_url = repository['source_url']


def init():
	if not os.path.isdir(plugins_dir):
		os.mkdir(plugins_dir)

	if os.path.isdir(build_dir):
		shutil.rmtree(build_dir)

	os.mkdir(build_dir)
	os.mkdir(build_temp_dir)


def build_plugins():
	addons_xml_root = etree.Element('addons')

	for plugin_info in plugins_info:
		name = plugin_info['name']
		print "processing: %s" % name

		if name == "":
			raise BaseException("plugin name is blank in configuration.")

		if "source_url" in plugin_info:
			_build_plugins_from_git(addons_xml_root, plugin_info)
		elif "repository_url" in plugin_info:
			_build_plugin_from_repository(addons_xml_root, plugin_info)
		elif "zip_url" in plugin_info:
			_build_plugin_from_zip(addons_xml_root, plugin_info)
		else:
			raise BaseException("Unable to process plugin")
	# remove temp path
	shutil.rmtree(build_temp_dir)

	xml_str = etree.tostring(addons_xml_root, pretty_print=True)
	addon_xml_file = os.path.join(build_plugins_dir, 'addons.xml')
	with open(addon_xml_file, 'w') as f:
		f.write(xml_str)

	_md5_hash_file(addon_xml_file)


def _build_plugin_from_zip(addons_xml_root, plugin_info):
	name = plugin_info['name']
	zip_url = plugin_info['zip_url']
	temp_extract_path = build_temp_dir
	local_filename = _download_file(zip_url, os.path.join(build_temp_dir, "%s.zip" % name))
	with zipfile.ZipFile(local_filename, 'r') as zip_ref:
		zip_ref.extractall(temp_extract_path)

	plugin_temp_path = os.path.join(temp_extract_path, name)
	build_plugin_path = os.path.join(build_plugins_dir, name)
	plugin_addon_xml = etree.parse(open(os.path.join(plugin_temp_path, 'addon.xml')))
	version = _get_version_from_addon_tree(plugin_addon_xml)
	name_with_version = "%s-%s" % (name, version)
	build_plugin_version_path = os.path.join(build_plugin_path, name_with_version)

	shutil.move(plugin_temp_path, build_plugins_dir)
	version_zip = "%s.zip" % build_plugin_version_path
	shutil.move(local_filename, version_zip)
	_md5_hash_file(version_zip)

	if os.path.exists(os.path.join(build_plugin_path, 'changelog.txt')):
		shutil.move(os.path.join(build_plugin_path, 'changelog.txt'),
		            os.path.join(build_plugin_path, 'changelog-%s.txt' % version))

	readmes = glob.glob1(build_plugin_path, "readme*")
	if len(readmes) > 0:
		readme = readmes[0]
		shutil.copy2(os.path.join(build_plugin_path, readme), os.path.join(build_plugin_path, "readme.md"))


	addons_xml_root.append(plugin_addon_xml.getroot())
	_cleanup_path(build_plugin_path)


def _build_plugins_from_git(addons_xml_root, plugin_info):
	name = plugin_info['name']
	source_url = plugin_info['source_url']

	if source_url.endswith('.git'):
		clone_url = source_url
		source_url = source_url[:-4]
	else:
		clone_url = "%s.git" % source_url

	repo_dir = os.path.join(plugins_dir, name)
	if not os.path.isdir(repo_dir):
		repo = git.Repo.clone_from(clone_url, repo_dir)
	else:
		repo = git.Repo(repo_dir)

	repo.remote().fetch()
	repo.head.reset(index=True, working_tree=True)

	tag_list = []
	for t in repo.tags:
		tag_list.append(t.name)
	# sort the tags as versions
	tag_list.sort(key=lambda x: LooseVersion(_get_version_from_tag(name, x)), reverse=True)

	if len(tag_list) == 0:
		# repo doesn't have any tags, so we will generate the repo from the 'latest'
		# we will get the version from the addon.xml
		_process_non_tagged_addon(repo, plugin_info, addons_xml_root)
	else:

		latest_processed = False
		for tag in tag_list:

			version = _get_version_from_tag(name, tag)
			if _is_tag_filtered_out(plugin_info, tag):
				continue

			repo.git.checkout('tags/%s' % tag)
			# try to download pre-existing zip from github releases

			try:
				if _process_github_release_addon(repo_dir, tag, plugin_info, addons_xml_root, latest_processed):
					latest_processed = True
			except Exception as err:
				print "download failed: {0}".format(err)
				if _process_non_release_addon(repo_dir, plugin_info, version, addons_xml_root, latest_processed):
					latest_processed = True


def _build_plugin_from_repository(addons_xml_root, plugin_info):
	name = plugin_info['name']
	repository_url = plugin_info["repository_url"]
	plugin_root_url = urlparse.urljoin(repository_url, "%s/" % name)
	html_data = http_request.get(plugin_root_url)
	beautiful_soup = BeautifulSoup(html_data, 'html.parser')
	a_entries = filter(lambda x: x.get('href') == x.contents[0],
	                   beautiful_soup.find_all("a", href=lambda x: not x.startswith("http")))
	items = []
	for a in a_entries:
		items.append(a.get('href'))
	# this checks if it has a bunch of files... some might not be 'requred'
	if not _can_process_repository_plugin(items):
		print "required file missing"
		return

	build_plugin_path = os.path.join(build_plugins_dir, name)
	if not os.path.exists(build_plugin_path):
		os.mkdir(build_plugin_path)

	for file_name in items:
		out_file = os.path.join(build_plugin_path, file_name)
		dl_url = urlparse.urljoin(plugin_root_url, file_name)
		_download_file(dl_url, out_file)

	if not _repository_has_zip_md5(items):
		zips = fnmatch.filter(items, "*.zip")
		for z in zips:
			zfile = os.path.join(build_plugin_path, z)
			md5file = os.path.join(build_plugin_path, "%s.md5")
			if not os.path.exists(md5file):
				_md5_hash_file(zfile)

	plugin_addon_xml = etree.parse(open(os.path.join(build_plugin_path, 'addon.xml')))
	version = _get_version_from_addon_tree(plugin_addon_xml)
	if os.path.exists(os.path.join(build_plugin_path, 'changelog.txt')):
		shutil.move(os.path.join(build_plugin_path, 'changelog.txt'),
		            os.path.join(build_plugin_path, 'changelog-%s.txt' % version))

	readmes = glob.glob1(build_plugin_path, "readme*")
	if len(readmes) > 0:
		readme = readmes[0]
		shutil.copy2(os.path.join(build_plugin_path, readme), os.path.join(build_plugin_path, "readme.md"))


	addons_xml_root.append(plugin_addon_xml.getroot())
	_cleanup_path(build_plugin_path)


def _process_github_release_addon(repo_dir, tag, plugin_info, addons_xml_root, latest_processed):
	name = plugin_info["name"]
	version = _get_version_from_tag(name, tag)
	source_url = plugin_info["source_url"]

	if not source_url.startswith("http://github.com/") and not source_url.startswith("https://github.com/"):
		# only github releases are currently supported.
		# if it is not github, then don't even try to get it, it will just fail.
		return _process_non_release_addon(repo_dir, name, version, addons_xml_root, latest_processed)

	if source_url.endswith('.git'):
		source_url = source_url[:-4]
	addons_xml_added = False
	name_with_version = "%s-%s" % (name, version)

	build_plugin_path = os.path.join(build_plugins_dir, name)
	build_plugin_version_path = os.path.join(build_plugin_path, name_with_version)

	temp_extract_path = build_temp_dir
	if not os.path.exists(temp_extract_path):
		os.mkdir(temp_extract_path)

	try:
		release_zip_url = '%s/releases/download/%s/%s.zip' % (source_url, tag, name_with_version)
		print release_zip_url
		local_filename = _download_file(release_zip_url, build_temp_dir)
		with zipfile.ZipFile(local_filename, 'r') as zip_ref:
			zip_ref.extractall(temp_extract_path)
	except Exception as oops:
		try:
			# some break the rules and put the v in the package... lets fix it.
			release_zip_url = '%s/releases/download/%s/%s-v%s.zip' % (source_url, tag, name, version)
			local_filename = _download_file(release_zip_url, os.path.join(build_temp_dir, "%s.zip" % name_with_version))
			with zipfile.ZipFile(local_filename, 'r') as zip_ref:
				zip_ref.extractall(temp_extract_path)
		except Exception as ex1:
			print "error downloading: %s" % source_url
			# try:
			# 	# some break the rules and put the v in the package... lets fix it.
			# 	release_zip_url = '%s/archive/%s-v%s.zip' % (source_url, name, version)
			# 	local_filename = _download_file(release_zip_url, os.path.join(build_temp_dir, "%s.zip" % name_with_version))
			# 	with zipfile.ZipFile(local_filename, 'r') as zip_ref:
			# 		zip_ref.extractall(temp_extract_path)
			# except Exception as ex2:
			# 	try:
			# 		# some break the rules and put the v in the package... lets fix it.
			# 		release_zip_url = '%s/archive/%s-v%s.zip' % (source_url, name, version)
			# 		local_filename = _download_file(release_zip_url, os.path.join(build_temp_dir, "%s.zip" % name_with_version))
			# 		with zipfile.ZipFile(local_filename, 'r') as zip_ref:
			# 			zip_ref.extractall(temp_extract_path)
			# 	except Exception as ex3:
			# 		try:
			# 			release_zip_url = '%s/archive/%s.zip' % (source_url, tag)
			# 			print release_zip_url
			# 			local_filename = _download_file(release_zip_url, build_temp_dir)
			# 			with zipfile.ZipFile(local_filename, 'r') as zip_ref:
			# 				zip_ref.extractall(temp_extract_path)
			# 		except Exception as ex4:
			# 			release_zip_url = '%s/archive/%s.zip' % (source_url, tag)
			# 			print release_zip_url
			# 			local_filename = _download_file(release_zip_url, build_temp_dir)
			# 			with zipfile.ZipFile(local_filename, 'r') as zip_ref:
			# 				zip_ref.extractall(temp_extract_path)

	plugin_addon_xml = etree.parse(open(os.path.join(temp_extract_path, name, 'addon.xml')))

	real_version = _get_version_from_addon_tree(plugin_addon_xml)
	if real_version != version:
		# the version from the tag is incorrect
		version = real_version
		name_with_version = "%s-%s" % (name, version)
		build_plugin_version_path = os.path.join(build_plugin_path, name_with_version)

	shutil.move(os.path.join(temp_extract_path, name), build_plugin_version_path)
	version_zip = os.path.join(build_plugin_version_path, "%s.zip" % name_with_version)
	shutil.move(local_filename, version_zip)

	_md5_hash_file(version_zip)

	readmes = glob.glob1(build_plugin_path, "readme*")
	if len(readmes) > 0:
		readme = readmes[0]
		shutil.copy2(os.path.join(build_plugin_path, readme), os.path.join(build_plugin_version_path, "readme.md"))

	if os.path.exists(os.path.join(build_plugin_version_path, 'changelog.txt')):
		shutil.move(os.path.join(build_plugin_version_path, 'changelog.txt'),
		            os.path.join(build_plugin_version_path, 'changelog-%s.txt' % version))

	# put latest in root
	latest_icon = os.path.join(build_plugin_path, "icon.png")
	latest_fanart = os.path.join(build_plugin_path, "fanart.jpg")

	latest_files = [latest_icon, latest_fanart]
	for l in latest_files:
		if os.path.exists(l):
			os.remove(l)

	shutil.move(version_zip, os.path.join(build_plugin_path, "%s.zip" % name_with_version))
	shutil.move("%s.md5" % version_zip, os.path.join(build_plugin_path, "%s.zip.md5" % name_with_version))

	if os.path.exists(os.path.join(build_plugin_version_path, 'readme.md')):
		shutil.copy2(os.path.join(build_plugin_version_path, 'readme.md'),
		             os.path.join(build_plugin_path, 'readme.md'))


	if os.path.exists(os.path.join(build_plugin_version_path, 'changelog-%s.txt' % version)):
		shutil.copy2(os.path.join(build_plugin_version_path, 'changelog-%s.txt' % version),
		             os.path.join(build_plugin_path, 'changelog-%s.txt' % version))

	if os.path.exists(os.path.join(build_plugin_version_path, "fanart.jpg")):
		shutil.copy2(os.path.join(build_plugin_version_path, "fanart.jpg"), latest_fanart)
	# according to the spec, this MUST exist in the plugin
	shutil.copy2(os.path.join(build_plugin_version_path, "icon.png"), latest_icon)

	# Only add the latest version to this
	if not latest_processed:
		addons_xml_root.append(plugin_addon_xml.getroot())
		addons_xml_added = True
	shutil.rmtree(build_plugin_version_path)
	return addons_xml_added


def _process_non_tagged_addon(repo, plugin_info, addons_xml_root):
	name = plugin_info["name"]
	repo_dir = os.path.join(plugins_dir, name)
	plugin_info_path = plugin_info["path"] if "path" in plugin_info else ""
	repo_plugin_dir = os.path.join(repo_dir, plugin_info_path)
	repo.git.checkout("HEAD")

	if not _can_process_non_tagged(repo_plugin_dir):
		print "unable to process because required files are missing"
		return

	plugin_addon_xml = etree.parse(open(os.path.join(repo_plugin_dir, 'addon.xml')))
	version = _get_version_from_addon_tree(plugin_addon_xml)

	_process_non_release_addon(repo_dir, plugin_info, version, addons_xml_root, False)


# checks for the 'required' files to process
def _can_process_non_tagged(repo_dir):
	# if not os.path.isfile(os.path.join(repo_dir, "changelog.txt")):
	# 	return False
	if not os.path.isfile(os.path.join(repo_dir, "icon.png")):
		return False
	if not os.path.isfile(os.path.join(repo_dir, "addon.xml")):
		return False
	return True


def _can_process_repository_plugin(item_list):
	if "addon.xml" not in item_list:
		return False
	if "icon.png" not in item_list:
		return False
	if len(fnmatch.filter(item_list, "*.zip")) == 0:
		return False
	return True


def _repository_has_zip_md5(item_list):
	if len(fnmatch.filter(item_list, "*.zip.md5")) != len(fnmatch.filter(item_list, "*.zip")):
		return False
	return True


def _get_version_from_addon_tree(addon_tree):
	return addon_tree.getroot().attrib["version"]


def _process_non_release_addon(repo_dir, plugin_info, version, addons_xml_root, latest_processed):
	name = plugin_info["name"]
	addons_xml_added = False
	name_with_version = "%s-%s" % (name, version)
	temp_extract_path = build_temp_dir
	build_plugin_path = os.path.join(build_plugins_dir, name)
	build_plugin_version_path = os.path.join(build_plugin_path, name_with_version)
	if os.path.isfile(os.path.join(build_temp_dir, "%s.zip" % name_with_version)):
		os.remove(os.path.join(build_temp_dir, "%s.zip" % name_with_version))
	build_repo_path = os.path.join(temp_extract_path, name)
	# copy the git repo to build_repo_path
	plugin_info_path = plugin_info["path"] if "path" in plugin_info else ""

	joined_repo_path = os.path.join(repo_dir, plugin_info_path)
	shutil.copytree(joined_repo_path, build_repo_path, ignore=shutil.ignore_patterns('.git*'))

	if len(glob.glob1(build_repo_path, "readme*")) < 1:
		treadmes = glob.glob1(repo_dir, "readme*")
		if len(treadmes) > 0:
			shutil.copy2(os.path.join(repo_dir, treadmes[0]), os.path.join(build_repo_path, "readme.md"))

	plugin_addon_xml = etree.parse(open(os.path.join(build_repo_path, 'addon.xml')))
	real_version = _get_version_from_addon_tree(plugin_addon_xml)
	if real_version != version:
		# the version from the tag is incorrect
		version = real_version
		name_with_version = "%s-%s" % (name, version)
		build_plugin_version_path = os.path.join(build_plugin_path, name_with_version)

	shutil.make_archive(build_plugin_version_path, 'zip', temp_extract_path, name)
	_md5_hash_file("%s.zip" % build_plugin_version_path)

	if not latest_processed:
		addons_xml_root.append(plugin_addon_xml.getroot())
		addons_xml_added = True
	_cleanup_path(build_repo_path)

	latest_icon = os.path.join(build_plugin_path, "icon.png")
	latest_fanart = os.path.join(build_plugin_path, "fanart.jpg")

	latest_files = [latest_icon, latest_fanart]
	for l in latest_files:
		if os.path.exists(l):
			os.remove(l)

	if os.path.exists(os.path.join(build_repo_path, 'changelog.txt')):
		shutil.move(os.path.join(build_repo_path, 'changelog.txt'),
		            os.path.join(build_plugin_path, 'changelog-%s.txt' % version))

	readmes = glob.glob1(build_repo_path, "readme*")
	if len(readmes) > 0:
		readme = readmes[0]
		shutil.copy2(os.path.join(build_repo_path, readme), os.path.join(build_plugin_path, "readme.md"))

	if os.path.exists(os.path.join(build_repo_path, "fanart.jpg")):
		shutil.move(os.path.join(build_repo_path, "fanart.jpg"), latest_fanart)
	# according to the spec, this MUST exist in the plugin
	shutil.move(os.path.join(build_repo_path, "icon.png"), latest_icon)
	shutil.rmtree(build_repo_path)
	return addons_xml_added


def _get_version_from_tag(plugin_name, tag):
	out_tag = tag
	lname = "%s-" % plugin_name
	if tag.startswith(lname):
		out_tag = out_tag[len(lname):]
	if out_tag.startswith("v"):
		out_tag = out_tag[1:]
	if out_tag.endswith(".zip"):
		out_tag = out_tag[:-4]
	return out_tag


def _is_tag_filtered_out(plugin, tag):
	tag_exclude = plugin.get('tag_exclude_pattern', [])
	tag_include = plugin.get('tag_include_pattern', ["*"])

	it_filtered = False
	# include filter
	for it in tag_include:
		if not fnmatch.fnmatch(tag, it):
			it_filtered = True
			break
	if it_filtered:
		return True

	it_filtered = False
	# exclude filter
	for et in tag_exclude:
		if fnmatch.fnmatch(tag, et):
			it_filtered = True
			break
	if it_filtered:
		return True

	return False


def _md5_hash_file(file_name):
	hash_md5 = hashlib.md5()
	with open(file_name, "rb") as f:
		for chunk in iter(lambda: f.read(4096), b""):
			hash_md5.update(chunk)

	with open("%s.md5" % file_name, 'w') as f:
		f.write(hash_md5.hexdigest())


def _get_file_contents(file_name):
	data = ""
	with open(file_name, "rb") as f:
		for chunk in iter(lambda: f.read(4096), b""):
			data += unicode(chunk, 'utf-8')
	return data


def _download_file(url, dest):
	if os.path.isdir(dest):
		local_filename = os.path.join(dest, url.split('/')[-1])
	else:
		local_filename = dest
	req = requests.get(url, stream=True)
	with open(local_filename, 'wb') as f:
		for chunk in req.iter_content(chunk_size=1024):
			if chunk:  # filter out keep-alive new chunks
				f.write(chunk)
	return local_filename


def _cleanup_path(path):
	for f in os.listdir(path):
		if f.startswith('changelog') or f.startswith('fanart.') or f.startswith('icon.') or \
				f.endswith('.zip') or f.startswith("readme") or f.startswith("README"):
			pass
		else:
			_f = os.path.join(path, f)
			if os.path.isdir(_f):
				shutil.rmtree(_f)
			else:
				os.remove(_f)


def build_gh_pages(root, current_dir):
	cur_dir = os.path.join(root, current_dir)
	print "building index.html for %s/" % current_dir

	pth = os.path.relpath(cur_dir, root)
	if pth == '.':
		pth = ''

	index_path = os.path.join('/', pth)
	heading_image = ""
	if os.path.exists(os.path.join(cur_dir, "icon.png")):
		heading_image = "<img src=\"./icon.png\" style=\"width:48px;height:48;margin-right:10px;\" alt=\"Index of %s\" />" % index_path
	html = "<html><head><title>Index of %s</title><body><h1>%sIndex of %s</h1><hr/><pre>" \
	       % (index_path, heading_image, index_path)
	item = './' if index_path == '/' else '../'
	html += "<a href=\"%s\">%s</a>\n" % (item, "../")

	dir_items = os.listdir(cur_dir)
	page_footer = ""
	for item in dir_items:
		item_path = os.path.join(cur_dir, item)
		if os.path.isdir(item_path):
			html += "<a href=\"%s/\">%s/</a>\n" % (item, item)

			build_gh_pages(root, os.path.join(current_dir, item))
		else:
			if item.startswith("readme"):
				try:
					page_footer = mistune.markdown(_get_file_contents(os.path.join(cur_dir, item)))\
						.replace('&lt;', '<')\
						.replace('&gt;', '>')
				except UnicodeDecodeError as mde:
					print mde.message
					pass

			html += "<a href=\"%s\">%s</a>\n" % (item, item)
	ts = datetime.datetime.now().strftime('%d-%b-%Y %H:%M')
	doc_version = os.getenv('CI_BUILD_VERSION', '1.0.0.0')
	if page_footer != "":
		pf = ("%s<hr/>" % page_footer)
	else:
		pf = ""
	html += "</pre><hr/>%s<div>Generated by <a href=\"%s\">%s</a> v%s at %s</div></body></html>" \
	        % (pf, repo_source_url, repo_name, doc_version, ts)

	with open(os.path.join(cur_dir, 'index.html'), 'w') as f:
		f.write(unicode(html))


def _get_source_url_from_plugin_info(plugin_info):
	if 'source_url' in plugin_info:
		return plugin_info['source_url']
	elif 'repository_url' in plugin_info:
		return plugin_info['repository_url']
	elif 'zip_url' in plugin_info:
		return plugin_info['zip_url']
	else:
		raise BaseException("Unable to locate source url")


def _build_gh_readme():
	print "generating readme"
	repo_version = ""
	data = []
	for plugin_info in plugins_info:
		name = plugin_info['name']
		source_url = _get_source_url_from_plugin_info(plugin_info)
		if source_url.endswith('.git'):
			source_url = source_url[:-4]
		pi_dir = os.path.join(build_plugins_dir, name)
		dir_items = glob.glob1(pi_dir, "*.zip")
		dir_items.sort(key=lambda x: LooseVersion(_get_version_from_tag(name, x)), reverse=True)
		if len(dir_items) >= 1:
			item = dir_items[0]
			if os.path.isfile(os.path.join(pi_dir, item)):
				if name == repo_name:
					repo_version = _get_version_from_tag(name, item)
				c = {
					"name": name,
					"version": _get_version_from_tag(name, item),
					"url": source_url
				}
				data.append(c)

	readme_file = os.path.join(build_plugins_dir, "readme.md")
	if os.path.exists(readme_file):
		os.remove(readme_file)
	md = u"# [%s](%s)\n\n|  | Plugin | Version | Download |\n| ----- | ----- | ----- | ----- |\n" \
	           % (repo_name, repo_url)
	for pd in data:
		dl = "%s/%s/%s-%s.zip" % (repo_url, pd["name"], pd["name"], pd["version"])
		md5 = "%s.md5" % dl
		# https://github.com/camalot/repository.camalot/raw/gh-pages/plugin.image.kodur/icon.png
		md += \
			u"| <img src=\"%s/raw/gh-pages/%s/icon.png\" width=\"24\" /> | [%s](%s) | %s | [[DL](%s)] [[MD5](%s)] |\n" \
			% (repo_source_url, pd["name"], pd["name"], pd["url"], pd["version"], dl, md5)
	ts = datetime.datetime.now().strftime('%d-%b-%Y %H:%M')
	doc_version = os.getenv('CI_BUILD_VERSION', '1.0.0.0')

	md += u"----\n\nRepository version %s - %s\n\n----\n" % (doc_version, ts)

	with open('.ghp_readme.md', 'r') as ghtf:
		data = ghtf.read()\
			.replace('#{REPO_URL}', repo_url)\
			.replace("#{REPO_NAME}", repo_name)\
			.replace("#{REPO_VERSION}", repo_version)

	md += u"\n%s\n" % data

	with open(readme_file, 'w') as f:
		f.write(md)


@click.command()
def run():
	init()
	build_plugins()
	_build_gh_readme()
	build_gh_pages(os.path.abspath(build_dir), '')


if __name__ == "__main__":
	run()
