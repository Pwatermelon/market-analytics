' КОНТРОЛЬНОЕ ЗАДАНИЕ 8
' Определение наличия корней функции на интервале
' Вариант 07: F_07(x) = Ax^0.5 + B + B * sinh(Ax)
' Расширенная версия задания 4 с графиком и детальным анализом

Option Explicit

' Функция F_07(x) = Ax^0.5 + B + B * sinh(Ax)
Function F07(x As Double, A As Double, B As Double) As Double
    If x < 0 Then
        F07 = 0
        Exit Function
    End If
    F07 = A * Sqr(x) + B + B * Application.WorksheetFunction.Sinh(A * x)
End Function

' Производная функции F_07(x)
Function F07_Proizvodnaya(x As Double, A As Double, B As Double) As Double
    If x <= 0 Then
        F07_Proizvodnaya = 0
        Exit Function
    End If
    ' f'(x) = A/(2*√x) + B*A*cosh(Ax)
    F07_Proizvodnaya = A / (2 * Sqr(x)) + B * A * Application.WorksheetFunction.Cosh(A * x)
End Function

' Проверка наличия корня на интервале [x1, x2]
Function EstKoren(x1 As Double, x2 As Double, A As Double, B As Double) As Boolean
    Dim f1 As Double, f2 As Double
    
    f1 = F07(x1, A, B)
    f2 = F07(x2, A, B)
    
    EstKoren = (f1 * f2 <= 0)
End Function

' Поиск всех корней на интервале методом деления пополам
Function NaytiVseKorni(x1 As Double, x2 As Double, A As Double, B As Double, _
                       Optional shag As Double = 0.1, Optional tochnost As Double = 0.0001) As Variant
    Dim korni() As Double
    Dim kolichestvoKorney As Integer
    Dim x As Double
    Dim xPrev As Double
    Dim fPrev As Double, fCurr As Double
    Dim koren As Double
    Dim i As Integer
    
    ReDim korni(1 To 100) ' Максимум 100 корней
    kolichestvoKorney = 0
    
    xPrev = x1
    fPrev = F07(xPrev, A, B)
    
    x = x1 + shag
    Do While x <= x2
        fCurr = F07(x, A, B)
        
        ' Если знак изменился, ищем корень
        If fPrev * fCurr < 0 Then
            koren = NaytiKorenBisektsiya(xPrev, x, A, B, tochnost)
            If Not IsError(koren) Then
                kolichestvoKorney = kolichestvoKorney + 1
                korni(kolichestvoKorney) = koren
            End If
        End If
        
        xPrev = x
        fPrev = fCurr
        x = x + shag
    Loop
    
    ' Возвращаем массив корней
    If kolichestvoKorney > 0 Then
        ReDim Preserve korni(1 To kolichestvoKorney)
        NaytiVseKorni = korni
    Else
        NaytiVseKorni = Array()
    End If
End Function

' Метод бисекции для поиска корня
Function NaytiKorenBisektsiya(x1 As Double, x2 As Double, A As Double, B As Double, _
                              Optional tochnost As Double = 0.0001) As Double
    Dim xLeft As Double, xRight As Double, xMid As Double
    Dim fLeft As Double, fRight As Double, fMid As Double
    Dim iterations As Integer
    Dim maxIterations As Integer
    
    xLeft = x1
    xRight = x2
    maxIterations = 100
    iterations = 0
    
    fLeft = F07(xLeft, A, B)
    fRight = F07(xRight, A, B)
    
    If fLeft * fRight > 0 Then
        NaytiKorenBisektsiya = CVErr(xlErrNA)
        Exit Function
    End If
    
    Do While (xRight - xLeft) > tochnost And iterations < maxIterations
        xMid = (xLeft + xRight) / 2
        fMid = F07(xMid, A, B)
        
        If Abs(fMid) < tochnost Then
            NaytiKorenBisektsiya = xMid
            Exit Function
        End If
        
        If fLeft * fMid < 0 Then
            xRight = xMid
            fRight = fMid
        Else
            xLeft = xMid
            fLeft = fMid
        End If
        
        iterations = iterations + 1
    Loop
    
    NaytiKorenBisektsiya = (xLeft + xRight) / 2
End Function

' Основная процедура анализа корней
Sub AnalizKorneyFunktsii()
    Dim x1 As Double, x2 As Double
    Dim A As Double, B As Double
    Dim korni As Variant
    Dim i As Integer
    Dim row As Integer
    
    ' Получение параметров из ячеек
    x1 = Range("B1").Value
    x2 = Range("B2").Value
    A = Range("B3").Value
    B = Range("B4").Value
    
    ' Проверка параметров
    If x1 >= x2 Then
        MsgBox "x1 dolzhno byt menshe x2!", vbExclamation
        Exit Sub
    End If
    
    ' Очистка результатов
    Range("D1:H1000").Clear
    
    ' Заголовки
    Range("D1").Value = "Analiz korney funktsii F_07(x)"
    Range("D2").Value = "Parametry:"
    Range("D3").Value = "A ="
    Range("E3").Value = A
    Range("D4").Value = "B ="
    Range("E4").Value = B
    Range("D5").Value = "Interval:"
    Range("E5").Value = "[" & x1 & "; " & x2 & "]"
    
    ' Проверка наличия корня
    Range("D7").Value = "Nalichie kornya:"
    If EstKoren(x1, x2, A, B) Then
        Range("E7").Value = "DA"
        Range("E7").Font.Color = RGB(0, 200, 0)
    Else
        Range("E7").Value = "NET"
        Range("E7").Font.Color = RGB(200, 0, 0)
    End If
    
    ' Поиск корней
    korni = NaytiVseKorni(x1, x2, A, B)
    
    If IsArray(korni) And UBound(korni) >= 1 Then
        Range("D9").Value = "Naydennye korni:"
        Range("D10").Value = "N"
        Range("E10").Value = "x"
        Range("F10").Value = "f(x)"
        Range("G10").Value = "f'(x)"
        
        row = 11
        For i = 1 To UBound(korni)
            Range("D" & row).Value = i
            Range("E" & row).Value = korni(i)
            Range("F" & row).Value = F07(korni(i), A, B)
            Range("G" & row).Value = F07_Proizvodnaya(korni(i), A, B)
            row = row + 1
        Next i
        
        MsgBox "Naydeno korney: " & UBound(korni), vbInformation
    Else
        Range("D9").Value = "Korni ne naydeny na dannom intervale"
        MsgBox "Korni ne naydeny na intervale [" & x1 & "; " & x2 & "]", vbInformation
    End If
    
    ' Построение таблицы значений для графика
    SozdatTablitsuDlyaGrafika x1, x2, A, B
End Sub

' Создание таблицы значений функции для построения графика
Sub SozdatTablitsuDlyaGrafika(x1 As Double, x2 As Double, A As Double, B As Double)
    Dim x As Double
    Dim shag As Double
    Dim row As Integer
    Dim kolichestvoTochek As Integer
    
    kolichestvoTochek = 50
    shag = (x2 - x1) / kolichestvoTochek
    
    ' Очистка
    Range("I1:J1000").Clear
    
    ' Заголовки
    Range("I1").Value = "x"
    Range("J1").Value = "f(x)"
    
    row = 2
    x = x1
    Do While x <= x2
        Range("I" & row).Value = x
        Range("J" & row).Value = F07(x, A, B)
        x = x + shag
        row = row + 1
    Loop
    
    ' Форматирование
    Range("I1:J1").Font.Bold = True
    Range("I:J").NumberFormat = "0.00"
End Sub

' ИНСТРУКЦИЯ:
' 1. Создайте таблицу в Excel:
'    A1: x1
'    B1: 0.1
'    A2: x2
'    B2: 10
'    A3: A
'    B3: 1
'    A4: B
'    B4: -5
'
' 2. Запустите макрос AnalizKorneyFunktsii()
'
' 3. Результаты появятся в столбцах D-J:
'    - D1-D5: Параметры функции
'    - D7-E7: Наличие корня
'    - D10-G10: Заголовки таблицы корней
'    - D11-G...: Найденные корни
'    - I1-J...: Таблица значений для графика
'
' 4. Постройте график на основе данных в столбцах I и J
