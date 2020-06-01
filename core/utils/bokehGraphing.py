from math import pi
from bokeh.plotting import figure, output_file, show
from bokeh.palettes import brewer
from bokeh.transform import cumsum
from bokeh.embed import components
import pandas as pd

def drawPieChart(x, paletteType='Set1'):
    '''
    Input: x --- Dictionary of names and values
           (e.g. x = {'United States': 157, 'United Kingdom': 93}
    '''

    data = pd.Series(x).reset_index(name='value').rename(columns={'index':'country'})
    data['angle'] = data['value']/data['value'].sum() * 2*pi

    colors = brewer[paletteType][8]
    data['color'] = colors[:len(x)]

##    p = figure(plot_height=350, title="Pie Chart", toolbar_location=None,
##               tools="hover", tooltips="@country: @value", x_range=(-0.5, 1.0))

    p = figure(plot_height=350, toolbar_location=None,
               tools="hover", tooltips="@country: @value", x_range=(-0.5, 1.0))

    p.wedge(x=0, y=1, radius=0.4,
        start_angle=cumsum('angle', include_zero=True), end_angle=cumsum('angle'),
        line_color="white", fill_color='color', legend_field='country', source=data)

    p.axis.axis_label=None
    p.axis.visible=False
    p.grid.grid_line_color = None
    p.outline_line_color = None

    p.sizing_mode = 'scale_width'

    script, div = components(p)

    return script, div
