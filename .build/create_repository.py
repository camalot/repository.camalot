from lxml import etree
import click
import datetime
import git
import json
import shutil
import os
import hashlib
import fnmatch
import requests
import zipfile
from distutils.version import LooseVersion, StrictVersion

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
		print name
		github_url = plugin_info['github_url']

		if github_url.endswith('.git'):
			clone_url = github_url
			github_url = github_url[:-4]
		else:
			clone_url = "%s.git" % github_url

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
		tag_list.sort(key=lambda x: LooseVersion(_get_version_from_tag(x)), reverse=True)

		latest_processed = False

		for tag in tag_list:
			version = _get_version_from_tag(tag)

			if _is_tag_filtered_out(plugin_info, tag):
				continue

			repo.git.checkout('tags/%s' % tag)

			changelog_file = os.path.join(repo_dir, "changelog.txt")
			if not os.path.isfile(changelog_file):
				print "skipping: %s - No changelog" % version
				continue

			name_with_version = '%s-%s' % (name, version)
			print name_with_version

			build_plugin_path = os.path.join(build_plugins_dir, name)
			build_plugin_version_path = os.path.join(build_plugin_path, name_with_version)
			# try to download pre-existing zip from github releases
			try:
				temp_extract_path = build_temp_dir
				if not os.path.exists(temp_extract_path):
					os.mkdir(temp_extract_path)
				release_zip_url = '%s/releases/download/%s/%s.zip' % (github_url, tag, name_with_version)
				local_filename = _download_file(release_zip_url, build_temp_dir)

				zip_ref = zipfile.ZipFile(local_filename, 'r')
				zip_ref.extractall(temp_extract_path)
				zip_ref.close()

				shutil.move(os.path.join(temp_extract_path, name), build_plugin_version_path)
				version_zip = os.path.join(build_plugin_version_path, "%s.zip" % name_with_version)
				shutil.move(local_filename, version_zip)

				_md5_hash_file(version_zip)

				plugin_addon_xml = etree.parse(open(os.path.join(build_plugin_version_path, 'addon.xml')))
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
					latest_processed = True
				shutil.rmtree(build_plugin_version_path)
			except Exception as err:
				print "download failed: {0}".format(err)
				# need to refactor so it behaves like the above
				build_repo_path = os.path.join(build_plugins_dir, name_with_version)
				shutil.copytree(repo_dir, build_repo_path, ignore=shutil.ignore_patterns('.git*'))
				shutil.make_archive(build_repo_path, 'zip', build_plugins_dir, name_with_version)
				shutil.move('%s.zip' % build_repo_path, build_repo_path)
				plugin_addon_xml = etree.parse(open(os.path.join(build_repo_path, 'addon.xml')))
				if not latest_processed:
					addons_xml_root.append(plugin_addon_xml.getroot())
					latest_processed = True
				_cleanup_path(build_repo_path)
				shutil.move(os.path.join(build_repo_path, 'changelog.txt'),
				            os.path.join(build_repo_path, 'changelog-%s.txt' % version))
				shutil.move(build_repo_path, os.path.join(build_plugins_dir, name))

	# remove temp path
	shutil.rmtree(build_temp_dir)

	xml_str = etree.tostring(addons_xml_root, pretty_print=True)
	addon_xml_file = os.path.join(build_plugins_dir, 'addons.xml')
	with open(addon_xml_file, 'w') as f:
		f.write(xml_str)

	_md5_hash_file(addon_xml_file)


def _get_version_from_tag(tag):
	out_tag = tag
	lname = "%s-" % out_tag
	if tag.startswith(lname):
		out_tag = out_tag[len(lname):]
	if out_tag.startswith("v"):
		out_tag = out_tag[1:]
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
				f.endswith('.zip'):
			pass
		else:
			_f = os.path.join(path, f)
			if os.path.isdir(_f):
				shutil.rmtree(_f)
			else:
				os.remove(_f)


def build_gh_pages(root, current_dir):
	cur_dir = os.path.join(root, current_dir)

	pth = os.path.relpath(cur_dir, root)
	if pth == '.':
		pth = ''

	index_path = os.path.join('/', pth)
	html = "<html><head><title>Index of %s</title><body><h1>Index of %s</h1><hr/><pre>" % (index_path, index_path)
	item = '../'  # if index_path == '/' else '../'
	html += "<a href=\"%s\">%s</a>\n" % (item, "../")

	dir_items = os.listdir(cur_dir)
	for item in dir_items:
		item_path = os.path.join(cur_dir, item)
		if os.path.isdir(item_path):
			html += "<a href=\"%s/\">%s/</a>\n" % (item, item)

			build_gh_pages(root, os.path.join(current_dir, item))
		else:
			html += "<a href=\"%s\">%s</a>\n" % (item, item)
	ts = datetime.datetime.now().strftime('%d-%b-%Y %H:%M')
	doc_version = os.getenv('CI_BUILD_VERSION', '1.0.0.0')
	html += "</pre><hr/><div>Generated by <a href=\"%s\">%s</a> v%s at %s</div></body></html>" \
	        % (repo_url, repo_name, doc_version, ts)

	f = open(os.path.join(cur_dir, 'index.html'), 'w')
	f.write(html)
	f.close()


@click.command()
def run():
	init()
	build_plugins()
	build_gh_pages(os.path.abspath(build_dir), '')


if __name__ == "__main__":
	run()
