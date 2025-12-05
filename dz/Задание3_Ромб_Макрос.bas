' КОНТРОЛЬНОЕ ЗАДАНИЕ 3
' Вариант 7: Вычисление площади и углов ромба по его диагоналям
' Макрос с помощью макрорекордера, закрепленный за элементами управления

Sub VychislitParametriRomb()
    ' Макрос для вычисления параметров ромба
    ' Получаем значения диагоналей из ячеек
    Dim d1 As Double
    Dim d2 As Double
    Dim ploshad As Double
    Dim ugolAlfa As Double
    Dim ugolBeta As Double
    Dim storona As Double
    Dim perimetr As Double
    Const PI As Double = 3.14159265358979
    
    ' Читаем значения из ячеек B1 и B2
    d1 = Range("B1").Value
    d2 = Range("B2").Value
    
    ' Вычисляем параметры
    ploshad = (d1 * d2) / 2
    ugolAlfa = 2 * Atn(d2 / d1) * 180 / PI
    ugolBeta = 180 - ugolAlfa
    storona = Sqr((d1 / 2) ^ 2 + (d2 / 2) ^ 2)
    perimetr = 4 * storona
    
    ' Записываем результаты в ячейки
    Range("B3").Value = ploshad
    Range("B4").Value = ugolAlfa
    Range("B5").Value = ugolBeta
    Range("B6").Value = storona
    Range("B7").Value = perimetr
    
    ' Форматируем результаты
    Range("B3").NumberFormat = "0.00"
    Range("B4").NumberFormat = "0.00"
    Range("B5").NumberFormat = "0.00"
    Range("B6").NumberFormat = "0.00"
    Range("B7").NumberFormat = "0.00"
    
    ' Добавляем единицы измерения
    Range("C3").Value = "ед²"
    Range("C4").Value = "°"
    Range("C5").Value = "°"
    Range("C6").Value = "ед"
    Range("C7").Value = "ед"
    
    MsgBox "Параметры ромба вычислены!", vbInformation
End Sub

' ИНСТРУКЦИЯ ПО СОЗДАНИЮ:
' 1. Создайте таблицу в Excel:
'    A1: Диагональ 1
'    B1: 10
'    A2: Диагональ 2
'    B2: 8
'    A3: Площадь
'    A4: Угол α
'    A5: Угол β
'    A6: Сторона
'    A7: Периметр
'
' 2. Включите макрорекордер (Разработчик → Запись макроса)
' 3. Выполните вычисления вручную
' 4. Остановите запись
' 5. Или используйте готовый макрос выше
'
' 6. Добавьте кнопку:
'    - Разработчик → Вставить → Кнопка (Форма)
'    - Нарисуйте кнопку на листе
'    - Привяжите макрос "VychislitParametriRomb"
'
' 7. Альтернативно используйте элементы управления ActiveX:
'    - Разработчик → Вставить → Кнопка (ActiveX)
'    - Двойной клик по кнопке → вставьте код
'    - Private Sub CommandButton1_Click()
'        VychislitParametriRomb
'      End Sub

