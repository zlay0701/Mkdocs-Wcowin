@echo off
chcp 65001
:: chcp 65001 就是换成UTF-8代码页-
:: chcp 936 默认的GBK-
:: chcp 437 美国英语-

echo  "start..."

mkdocs serve

@pause