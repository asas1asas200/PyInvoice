from matplotlib.font_manager import FontProperties
from matplotlib.figure import Figure
from matplotlib.text import Text
from collections import Counter
from os import path

class Chart:
	def __init__(self, cnt, title, content):
		self.fig = Figure(figsize=(4, 6))
		self.font_lg = FontProperties(fname=path.abspath('../fonts/NotoSansTC-Regular.otf'), size=16)
		self.font_md = FontProperties(fname=path.abspath('../fonts/NotoSansTC-Regular.otf'), size=14)
		self.font_sm = FontProperties(fname=path.abspath('../fonts/NotoSansTC-Regular.otf'), size=10)
	#def calc_range_info(self, cnt, title, content):
		p = self.fig.gca()
		p.set_title(title + '\n' + content, fontproperties=self.font_lg, position=(0.5, 2.))
		p.pie(cnt.values(), shadow=True)
		p.legend(
			labels=[ i + ' - ' + str(cnt[i]) for i in cnt.keys() ],
			prop=self.font_sm,
			loc='lower center',
			ncol=3,
			bbox_to_anchor=(0.5, -0.4)
		)
		self.fig.subplots_adjust(left=0, right=1., top=1.2)
#		return self.fig
		
	

if __name__ == '__main__':
	chart = Chart()
