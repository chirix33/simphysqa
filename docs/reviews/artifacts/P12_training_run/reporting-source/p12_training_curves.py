"""Render saved run curves with ReportLab's standard LinePlot (no model calls)."""
import json
import math
from pathlib import Path
from reportlab.graphics.shapes import Drawing, String, Rect
from reportlab.graphics.charts.lineplots import LinePlot
from reportlab.graphics import renderSVG
from reportlab.lib.colors import HexColor

ROOT = Path(__file__).resolve().parents[1]
EXPORT = ROOT/'docs/reviews/artifacts/P12_training_run'


def draw():
    audit = json.loads((EXPORT/'audit.json').read_text())
    drawing = Drawing(920,1040)
    drawing.add(Rect(0,0,920,1040,fillColor=HexColor('#FFFFFF'),strokeColor=None))
    drawing.add(String(36,1008,'Phi-JEPA: training and validation curves',fontSize=20))
    drawing.add(String(36,987,'Seed 11 | batch 256 | original validation only | no convergence claim',fontSize=10))
    drawing.add(String(36,968,'Y axes show log10(value). Training is mean augmented-vector MSE within each pass interval.',fontSize=9))
    colors = ['#126D82','#7D4FA2','#BF6317','#367B47']
    for row,(domain,values) in enumerate(audit['domains'].items()):
        top = 930-row*222
        drawing.add(String(36,top,domain.replace('_',' '),fontSize=13))
        for col,(key,metric,label) in enumerate((
            ('training_curve','loss','log10(training augmented MSE)'),
            ('validation_curve','score','log10(validation normalized error)'))):
            data = [(r['pass'],math.log10(max(r[metric],1e-16))) for r in values[key]]
            x = 75+col*435
            y = top-170
            drawing.add(String(x,y-33,'Completed pass / scheduled pass interval',fontSize=9))
            drawing.add(String(x,y+150,label,fontSize=10))
            if not data:
                drawing.add(String(x,y+65,'No completed observations',fontSize=12))
                continue
            chart = LinePlot()
            chart.x,chart.y,chart.width,chart.height = x,y,340,133
            chart.data = [data]
            chart.lines[0].strokeColor = HexColor(colors[row])
            chart.lines[0].strokeWidth = 1.8
            chart.xValueAxis.valueMin,chart.xValueAxis.valueMax = 1,10
            chart.xValueAxis.valueSteps = list(range(1,11))
            chart.xValueAxis.labels.fontSize = 8
            chart.yValueAxis.labels.fontSize = 8
            chart.yValueAxis.labelTextFormat = '%.2f'
            chart.yValueAxis.visibleGrid = True
            chart.yValueAxis.gridStrokeColor = HexColor('#DDDDDD')
            low,high = min(v for _,v in data),max(v for _,v in data)
            pad = max(.05,(high-low)*.12)
            chart.yValueAxis.valueMin,chart.yValueAxis.valueMax = low-pad,high+pad
            drawing.add(chart)
            if col == 1 and values['selected']:
                chosen = next(r['pass'] for r in values[key] if r['update']==values['selected']['update'])
                drawing.add(String(x,y-47,f'Selected: pass {chosen}, update {values["selected"]["update"]}',fontSize=9))
    renderSVG.drawToFile(drawing,str(EXPORT/'training-validation-curves.svg'))
    print(EXPORT/'training-validation-curves.svg')


if __name__ == '__main__':
    draw()
