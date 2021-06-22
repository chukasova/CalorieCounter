from data_base import get_last_data
import pygal
from pygal.style import Style

custom_style = Style(colors=('#E80080', '#404040', '#9BC850'), title_font_size=4, legend_box_size=4, label_font_size=4)

result = get_last_data('438443343')

line_chart = pygal.Bar(width=400, height=200)
line_chart.title = 'Kcal last 7 days'
line_chart.x_labels = map(lambda x: x[2], result)
line_chart.add('kcal', list(map(lambda x: x[1], result)))
line_chart.render_in_browser()

