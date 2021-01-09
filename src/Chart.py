from os import path, getcwd
from matplotlib.figure import Figure
from matplotlib.font_manager import FontProperties

class PieChart(Figure):
	def __init__(self, cnt):
		super().__init__(figsize=(7, 5))
		fontpath = path.join(getcwd(), 'fonts', 'NotoSansTC-Regular.otf')
		self.font_lg = FontProperties(fname=fontpath, size=16)
		self.font_md = FontProperties(fname=fontpath, size=14)
		self.font_sm = FontProperties(fname=fontpath, size=10)
		self.data = cnt.most_common(24) # 25(max legend size) = 5(col) * 5(row)
		self.others = sum( i[1] for i in (set(cnt.items()) - set(self.data)) )
		if self.others:
			self.data.append(('其他項目', self.others))
		self.p = self.gca()
		self.p.pie([ i[1] for i in self.data ], shadow=True)
		self.p.legend(
			labels=[ key + ' - ' + str(val) for key, val in self.data ],
			prop=self.font_sm,
			loc='lower center',
			ncol=5,
			bbox_to_anchor=(0.5, -0.1)
		)
		self.subplots_adjust(left=0., right=1., top=1.05)