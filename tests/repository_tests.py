import unittest
import json


class RepositoryFileTests(unittest.TestCase):

	def test_plugin_section_is_described(self):
		config = json.load(open('.repository.json'))
		self.assertTrue("plugins" in config)

	def test_repository_section_is_described(self):
		config = json.load(open('.repository.json'))
		self.assertTrue("repository" in config)

	def test_all_plugins_have_name(self):
		config = json.load(open('.repository.json'))
		for p in config["plugins"]:
			self.assertTrue("name" in p, "Required property 'name' is missing")
			self.assertFalse(p["name"] == "", "A defined plugin is missing the name value")

	def test_all_plugins_have_url(self):
		config = json.load(open('.repository.json'))
		for p in config["plugins"]:
			self.assertTrue("source_url" in p or "zip_url" in p or "repository_url" in p,
			                "Plugin must define a source: [source_url, zip_url, repository_url")

	def test_repository_is_described(self):
		config = json.load(open('.repository.json'))
		repo = config['repository']
		self.assertTrue('id' in repo and repo['id'] != "", "Missing repository id")
		self.assertTrue('url' in repo and repo['url'] != "", "Missing repository url")
		self.assertTrue('source_url' in repo and repo['source_url'] != "", "Missing repository source_url")

	def test_repository_has_described_plugin(self):
		config = json.load(open('.repository.json'))
		repo = config['repository']
		rid = repo['id']
		found_id = False
		for p in config['plugins']:
			if p['name'] == rid:
				found_id = True

		self.assertTrue(found_id, "Missing plugin for the repository")


if __name__ == '__main__':
	unittest.main()
