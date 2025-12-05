' КОНТРОЛЬНОЕ ЗАДАНИЕ 7
' Вариант 7: Найти сумму значений числового диапазона ячеек
' Процедурное программирование

' Функция для вычисления суммы числового диапазона
Function SummaDiapazona(diapazon As Range) As Double
    Dim yacheyka As Range
    Dim summa As Double
    
    summa = 0
    
    For Each yacheyka In diapazon
        ' Проверяем, что ячейка содержит число
        If IsNumeric(yacheyka.Value) Then
            summa = summa + CDbl(yacheyka.Value)
        End If
    Next yacheyka
    
    SummaDiapazona = summa
End Function

' Процедура для вычисления суммы и вывода результата
Sub VychislitSummu()
    Dim diapazon As Range
    Dim summa As Double
    Dim adresDiapazona As String
    
    ' Получаем диапазон из ячейки B1 (адрес диапазона)
    On Error Resume Next
    adresDiapazona = Range("B1").Value
    
    If adresDiapazona = "" Then
        ' Если адрес не указан, используем выделенный диапазон
        If Selection.Cells.Count > 1 Then
            Set diapazon = Selection
        Else
            MsgBox "Vydelite diapazon yacheek ili ukazhite adres v yacheyke B1", vbExclamation
            Exit Sub
        End If
    Else
        Set diapazon = Range(adresDiapazona)
    End If
    
    On Error GoTo Oshibka
    
    ' Вычисляем сумму
    summa = SummaDiapazona(diapazon)
    
    ' Выводим результат в ячейку B2
    Range("B2").Value = summa
    
    ' Форматируем результат
    Range("B2").NumberFormat = "0.00"
    
    MsgBox "Summa diapazona " & diapazon.Address & " = " & summa, vbInformation
    
    Exit Sub
    
Oshibka:
    MsgBox "Oshibka! Proverte pravilnost ukazannogo diapazona.", vbCritical
End Sub

' Альтернативная процедура с указанием диапазона в параметрах
Sub VychislitSummuDiapazona(adresNachala As String, adresKontsa As String)
    Dim diapazon As Range
    Dim summa As Double
    
    On Error GoTo Oshibka
    
    Set diapazon = Range(adresNachala & ":" & adresKontsa)
    summa = SummaDiapazona(diapazon)
    
    ' Выводим результат в активную ячейку
    ActiveCell.Value = summa
    ActiveCell.NumberFormat = "0.00"
    
    Exit Sub
    
Oshibka:
    MsgBox "Oshibka pri vychislenii summy diapazona!", vbCritical
End Sub

' Процедура для вычисления суммы с использованием встроенной функции Excel
Sub SummaVstroennaya()
    Dim diapazon As Range
    Dim summa As Double
    
    ' Получаем выделенный диапазон
    If Selection.Cells.Count = 1 Then
        MsgBox "Vydelite diapazon yacheek dlya vychisleniya summy", vbExclamation
        Exit Sub
    End If
    
    Set diapazon = Selection
    
    ' Используем встроенную функцию SUM
    summa = Application.WorksheetFunction.Sum(diapazon)
    
    ' Выводим результат
    ActiveCell.Value = summa
    ActiveCell.NumberFormat = "0.00"
    
    MsgBox "Summa = " & summa, vbInformation
End Sub

' Процедура для создания таблицы с тестовыми данными
Sub SozdatTestovyeDannye()
    Dim i As Integer
    Dim sluchaynoyeChislo As Double
    
    ' Очистка диапазона A1:A10
    Range("A1:A10").Clear
    
    ' Заполнение случайными числами
    Randomize
    For i = 1 To 10
        sluchaynoyeChislo = Int((100 - 1 + 1) * Rnd + 1) ' Случайное число от 1 до 100
        Range("A" & i).Value = sluchaynoyeChislo
    Next i
    
    ' Заголовок
    Range("A1").Value = "Znacheniya"
    
    ' Вычисление суммы
    Range("A12").Value = "Summa:"
    Range("B12").Value = SummaDiapazona(Range("A2:A10"))
    
    MsgBox "Testovye dannye sozdany v stolbtse A", vbInformation
End Sub

' ИНСТРУКЦИЯ ПО ИСПОЛЬЗОВАНИЮ:
'
' ВАРИАНТ 1 - Использование функции в ячейке:
' 1. Выделите диапазон ячеек (например, A1:A10)
' 2. В ячейке B1 введите: =SummaDiapazona(A1:A10)
'
' ВАРИАНТ 2 - Использование процедуры:
' 1. В ячейке B1 укажите адрес диапазона (например, "A1:A10")
' 2. Запустите макрос VychislitSummu()
' 3. Результат появится в ячейке B2
'
' ВАРИАНТ 3 - Выделение диапазона:
' 1. Выделите диапазон ячеек
' 2. Запустите макрос VychislitSummu()
' 3. Результат появится в ячейке B2
'
' ВАРИАНТ 4 - Создание тестовых данных:
' 1. Запустите макрос SozdatTestovyeDannye()
' 2. Автоматически создастся таблица и вычислится сумма
