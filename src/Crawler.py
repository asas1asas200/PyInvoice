import requests
from bs4 import BeautifulSoup
from threading import Thread
from queue import Queue
from collections import namedtuple, Counter
import re

class Crawler:
	def __init__(self):
		self.home = 'https://www.etax.nat.gov.tw/'
		try:
			requests.get(self.home)
		except requests.exceptions.ConnectionError as Err:
			raise Err
		self.soup = self.parse_page('https://www.etax.nat.gov.tw/etw-main/web/ETW183W1/')
		self.q = Queue()
		self.pages = []	

	@staticmethod
	def parse_page(url):
		while True:	
			try:
				r = requests.get(url)
				break
			except requests.exceptions.ConnectionError:
				pass
		r.encoding = 'utf-8'
		soup = BeautifulSoup(r.text, 'html.parser')
		return soup

	@staticmethod
	def _crawling_pages(pages):
		def decorator(func):
			def wrap():
				threads = []
				for page in pages:
					t = Thread(target=func, args=(page,))
					t.start()
					threads.append(t)
				for t in threads:
					t.join()
				return wrap
			return wrap
		return decorator


class AnalyzeCrawler(Crawler):
	def __init__(self):
		super().__init__()
		self.Invoice = namedtuple('Invoice', ['com', 'addr', 'items', 'spent'])
		self.pages = [ self.home + i.find('a')['href'] for i in self.soup.find_all('td', {'headers': 'title'})[:-8:2] ]

	def crawling(self):
		@self._crawling_pages(self.pages)
		def get_invoices(url):
			def parse_addr(addr):
				addr = addr[:3]
				if addr == '台北市':
					addr = '臺北市'
				elif addr == '桃園縣':
					addr = '桃園市'
				return addr

			def parse_items(items):
				items = re.sub(r'[ ,]', '', items)
				match = re.search(r'[共計]?(\d*)元', items)
				if match:
					spent = int(match[1])
					items = re.sub(match[0], '', items)
				else:
					spent = -1
				items = re.sub(r'\d+[杯瓶罐項]', '', items)
				items = re.sub(r'\*\d*', '', items)
				items = re.sub(r'[共計等，。]', '', items)
				items = re.split(r'、|及', items)
				for idx, item in enumerate(items):
					if '應用程式' in item:
						items[idx] = '應用程式'
					elif '服務費' in item:
						items[idx] = '服務費'
					elif '遊戲點數' in item:
						items[idx] = '遊戲點數'
				return items, spent

			soup = self.parse_page(url)
			date = soup.find('a', {'data-toggle': 'tab'}).text[:-15]
			thousand = []
			two_hundred = []
			for html_id, price in (('fbonly', thousand), ('fbonly_200', two_hundred)): # 1000W and 200W
				for invoice in soup.find(id=html_id).select('tr')[1:]:
					com, addr, items = [i.text for i in invoice.select('td')[-3:]]
					addr = parse_addr(addr)
					items, spent = parse_items(items)
					price.append(self.Invoice(com, addr, items, spent))
			self.q.put({date: {'thousand': thousand, 'two_hundred': two_hundred}})

		get_invoices()
		self.invoices = {}
		while self.q.qsize():
			self.invoices.update(self.q.get())

	def get_date_range_info(self, earlier_date, later_date):
		dates = self.dates
		now = dates.index(later_date)
		thousand_addrs = Counter()
		thousand_items = Counter()
		two_hundred_addrs = Counter()
		two_hundred_items = Counter()
		while True:
			for price, obj in (('thousand', (thousand_addrs, thousand_items)), ('two_hundred', (two_hundred_addrs, two_hundred_items))):
				obj[0].update([ i.addr for i in self.invoices[dates[now]][price] ])
				for i in self.invoices[dates[now]][price]:
					obj[1].update(i.items)
			if dates[now] == earlier_date:
				break
			now += 1
		return [thousand_items, thousand_addrs, two_hundred_items, two_hundred_addrs]

	@property
	def dates(self):
		return sorted(self.invoices.keys(), reverse=True)

	def __get_property(self, attr):
		ret = []
		for i in self.invoices.values():
			for price in ('thousand', 'two_hundred'):
				for j in i[price]:
					ret.append(getattr(j, attr))
		return sorted(ret)
	@property
	def titles(self):
		return ['特別獎1000萬--交易項目', '特別獎1000萬--縣市', '特獎200萬--交易項目', '特獎200萬--縣市']

	@property
	def spents(self):
		return self.__get_property('spent')

	@property
	def items(self):
		return self.__get_property('items')

	@property
	def addrs(self):
		return self.__get_property('addr')

	@property
	def schedule(self):
		return (len(self.pages) if hasattr(self, 'invoices') else self.q.qsize(), len(self.pages))


class RedeemCrawler(Crawler):
	class PrizeInfo:
		def __init__(self, special_thousand, special_two_hundred, top, two_hundred):
			self.special_thousand = special_thousand
			self.special_two_hundred = special_two_hundred
			self.top = top
			self.two_hundred = two_hundred

	def __init__(self):
		super().__init__()
		self.pages = [ self.home + i.find('a')['href'] for i in self.soup.find_all('td', {'headers': 'title'})[1:-8:2] ]

	def crawling(self):
		@self._crawling_pages(self.pages)
		def get_prize_number(url):
			soup = self.parse_page(url)
			lst = soup.select('tbody tr')
			title = soup.find('td', {'class': 'title'}).text
			year = re.search(r'(\d+)年', title).group(1)
			months = [ int(i) for i in title.split()[1:4:2] ]
			info = self.PrizeInfo(
				re.search(r'\d+', lst[1].text).group(),
				re.search(r'\d+', lst[3].text).group(),
				re.search(r'((\d+).*)', lst[5].text).group().split(),
				[ i for i in re.split(r'[、 ]', re.search(r'((\d+).*)', lst[12].text).group()) if i ]
			)
			self.q.put(( year, [ (month, info) for month in months ] ))

		get_prize_number()
		self.prize_numbers = {}
		while self.q.qsize():
			now = self.q.get()
			try:
				self.prize_numbers[now[0]].extend(now[1])
			except KeyError:
				self.prize_numbers[now[0]] = now[1]
		for key, value in self.prize_numbers.items():
			self.prize_numbers[key] = dict(value)

	def get_price(self, number, year, month):
		price = {
			3: 200,
			4: 1000,
			5: 4000,
			6: 10000,
			7: 40000,
			8: 200000
		}
		if number == self.prize_numbers[year][month].special_thousand:
			return 10000000
		elif number == self.prize_numbers[year][month].special_two_hundred:
			return 2000000
		else:
			maxn = 0
			for target in self.prize_numbers[year][month].top + self.prize_numbers[year][month].two_hundred:
				buf = 0
				for i, j in zip(target[::-1], number[::-1]):
					if i == j:
						buf += 1
					else:
						break
				maxn = max(buf, maxn)
			try:
				return price[maxn]
			except KeyError:
				return 0

	@property
	def years(self):
		return sorted(self.prize_numbers.keys(), reverse=True)

	@property
	def schedule(self):
		return (len(self.pages) if hasattr(self, 'prize_numbers') else self.q.qsize(), len(self.pages))



if __name__ == '__main__':
	crawler = RedeemCrawler()
	crawler.crawling()