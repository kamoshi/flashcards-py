from typing import Tuple, List

from PySide2.QtCharts import QtCharts
from PySide2.QtGui import QPainter
from PySide2.QtWidgets import QDialog, QGridLayout


class DeckStatsWindow(QDialog):

    def __init__(self):
        super().__init__()
        self.setFixedSize(800, 400)
        self.setWindowTitle("Deck statistics")
        layout = QGridLayout()
        # graphs
        self.chartPieView = QtCharts.QChartView()
        self.chartPieView.setRenderHint(QPainter.Antialiasing)
        self.chartBarView = QtCharts.QChartView()
        # init
        layout.addWidget(self.chartPieView, 0, 0)
        layout.addWidget(self.chartBarView, 0, 1)
        self.setLayout(layout)

    def setPieChartData(self, data: List[Tuple[str, int]]):
        pieSeries = QtCharts.QPieSeries()
        for name, value in data:
            pieSeries.append(name, value)
        chartPie = QtCharts.QChart()
        chartPie.addSeries(pieSeries)
        chartPie.setAnimationOptions(QtCharts.QChart.SeriesAnimations)
        chartPie.setTitle("Note maturity")
        self.chartPieView.setChart(chartPie)

    def setBarChartData(self, data: List[int]):
        barSet = QtCharts.QBarSet("Days")
        barSet.append(data)
        series = QtCharts.QBarSeries()
        series.append(barSet)
        chartBar = QtCharts.QChart()
        chartBar.addSeries(series)
        chartBar.setTitle("Reviews by days")
        chartBar.setAnimationOptions(QtCharts.QChart.SeriesAnimations)
        self.chartBarView.setChart(chartBar)


class NoteStatsWindow(QDialog):

    def __init__(self):
        super().__init__()
        self.setFixedSize(400, 400)
        self.setWindowTitle("Note statistics")
        layout = QGridLayout()
        # graphs
        self.chartPieView = QtCharts.QChartView()
        self.chartPieView.setRenderHint(QPainter.Antialiasing)
        # init
        layout.addWidget(self.chartPieView, 0, 0)
        self.setLayout(layout)

    def setPieChartData(self, data: List[Tuple[str, int]]):
        pieSeries = QtCharts.QPieSeries()
        for name, value in data:
            pieSeries.append(name, value)
        chartPie = QtCharts.QChart()
        chartPie.addSeries(pieSeries)
        chartPie.setAnimationOptions(QtCharts.QChart.SeriesAnimations)
        chartPie.setTitle("Rating history")
        self.chartPieView.setChart(chartPie)
