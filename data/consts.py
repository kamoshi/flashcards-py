HTML_TEMPLATE = """<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0//EN" 
"http://www.w3.org/TR/REC-html40/strict.dtd"> <html><head><meta name="qrichtext" content="1" /><style 
type="text/css"> p, li { white-space: pre-wrap; } </style></head> <body style=" font-family:'MS Shell Dlg 2'; 
font-size:7.8pt; font-weight:400; font-style:normal;"> {{Body}} </body></html>"""

CARD_FRONT_TEMPLATE = """<center><h1>{{Field1}}</h1></center>"""

CARD_BACK_TEMPLATE = """{{FrontSide}}
</br>
</br>
<center>{{Field2}}</center>"""