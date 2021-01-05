import requests
from bs4 import BeautifulSoup
from threading import Thread
from queue import Queue
from collections import namedtuple, Counter
import re
class Crawler:
	def __init__(self):
		self.Invoice = namedtuple('Invoice', ['com', 'addr', 'items', 'spent'])
		self.home = 'https://www.etax.nat.gov.tw/'
		soup = self.parse_page('https://www.etax.nat.gov.tw/etw-main/web/ETW183W1/')
		self.pages = soup.find_all('td', {'headers': 'title'})[:-8:2]
		self.q = Queue()

	@staticmethod
	def parse_page(url):
		r = requests.get(url)
		r.encoding = 'utf-8'
		soup = BeautifulSoup(r.text, 'html.parser')
		return soup

	def crawling(self):
		def get_invoices(url, q):
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
			q.put({date: {'thousand': thousand, 'two_hundred': two_hundred}})

		threads = []
		for page in self.pages:
			t = Thread(target=get_invoices, args=(self.home + page.find('a')['href'], self.q))
			t.start()
			threads.append(t)
		for t in threads:
			t.join()
		self.invoices = {}
		while self.q.qsize():
			self.invoices.update(self.q.get())

	@property
	def schedule(self):
		return (len(self.pages) if hasattr(self, 'invoices') else self.q.qsize(), len(self.pages))

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
