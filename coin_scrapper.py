from requests_html import HTMLSession # we need it to request to the site "coinmarketcap.com"
# This package is based on "requests" package, but we didn't use requests package ourselves, because we could not create session. But by this package we could create session.
# Why did we need to create session. Because, in the site, after filling the page with html, some ajax javascript code executes to get paragraphs.
# And if we use the "requests" package, we take only html code that not filled with paragraphs, because, requests stops to wait response, and the data what is getted by ajax javascript code won't be in the response.
# So, we won't have paragraphs. But, by this package "requests_html", we create session, and session waits the response until server won't answer completely.
# So, by this, we will have paragraphs.

from bs4 import BeautifulSoup as BS # we need it to work with html code what responded from the server of the coinmarketcap.com
 
class Scrapper:
	def __init__(self): # constructor
		self.__url = "https://coinmarketcap.com/currencies/{cryptocurrency_name}/news/"
		self.last_result = [] # will save a scrapping last result
		self.session = HTMLSession() # Create session
		self.session.browser # Start session

	def get_news_of_cryptocurrency(self, cryptocurrency_name): # By calling this function we get scrapped paragraphs from coinmarketcap.com
		resp = self.session.get(self.__url.format(cryptocurrency_name = cryptocurrency_name)) # To request to the site using session
		try:
			resp.html.render(timeout=20.0) # Try to render the html code
		except:
			self.last_result = "Error" # If there is some error, last_result equals to "Error"
		else:
			soup = BS(resp.html.html, "html.parser") # Create BeautifulSoup object for working with responded html
			 
			news = [] # will contain paragraphs
			for j in soup.select(".svowul-5.czQlor"):
				title = j.select("h3")[0].get_text() # The title of the paragraphs in the site wrote in the "h3" tag. So we select "h3" tag and get text from this tag, we get text of paragraph's title
				content = j.select(".sc-1eb5slv-0.svowul-3.ddtKCV")[0].get_text()
				source = j.select(".sc-1eb5slv-0.svowul-7.gYmsIK")[0].get_text()
				published_time = j.select(".sc-1eb5slv-0.hykWbK")[0].get_text()
				cryptocurrency = j.select(".sc-1eb5slv-0.hQRknF")[0].get_text()
				url = j.select("a")[0]['href']
				if not url.startswith("http"):
					url = "https://coinmarketcap.com" + url
				news.append({"title": title, "content": content, "source": source, "published_time": published_time, "cryptocurrency": cryptocurrency, "url": url})
			
			self.last_result = news # after scrapping, the last_result attribute will save the paragraphs into itself
