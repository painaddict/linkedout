import sys, json
import requests
from loguru import logger
import config

class Linkedout(object):
	def __init__(self, slug):
		self.session = requests.Session()
		self.session.headers.update(config.HEADERS)
		self.session.cookies.update(config.COOKIES)
		self.slug = slug
		self.get_course_details()
	
	def get_course_details(self):
		s = self.session.get(url=config.BASE_URL + 'detailedLearningPaths', params={
    		'learningPathSlug': self.slug,
    		'q': 'slug',
    		'version': '2',
		}).json()
		logger.info(s)

	def check_validity(self):
		s = self.session.post(url=config.BASE_URL + )

@logger.catch
def main():
	slug = sys.argv[1]
	linkedout = Linkedout(slug)

if __name__ == "__main__":
	main()