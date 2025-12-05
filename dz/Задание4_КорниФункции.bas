' КОНТРОЛЬНОЕ ЗАДАНИЕ 4
' Вариант 07: Определение наличия корня функции F_07(x) = F_0 + F_7
' F_0 = Ax^0.5 + B
' F_7 = BSh(Ax) = B * sinh(Ax)
' F_07(x) = Ax^0.5 + B + B * sinh(Ax)
' Найти значения коэффициентов A и B, при которых есть корень на интервале [x1, x2]

Option Explicit

' Функция F_07(x) = Ax^0.5 + B + B * sinh(Ax)
Function F07(x As Double, A As Double, B As Double) As Double
    If x < 0 Then
        F07 = 0 ' Корень из отрицательного числа не определен
        Exit Function
    End If
    F07 = A * Sqr(x) + B + B * Application.WorksheetFunction.Sinh(A * x)
End Function

' Проверка наличия корня на интервале [x1, x2]
' Корень есть, если функция меняет знак (пересекает ось X)
Function EstKoren(x1 As Double, x2 As Double, A As Double, B As Double) As Boolean
    Dim f1 As Double, f2 As Double
    
    f1 = F07(x1, A, B)
    f2 = F07(x2, A, B)
    
    ' Если значения разных знаков, значит есть корень
    EstKoren = (f1 * f2 <= 0)
End Function

' Поиск корня методом деления пополам (бисекции)
Function NaytiKoren(x1 As Double, x2 As Double, A As Double, B As Double, _
                     Optional tochnost As Double = 0.0001) As Double
    Dim xLeft As Double, xRight As Double, xMid As Double
    Dim fLeft As Double, fRight As Double, fMid As Double
    Dim iterations As Integer
    Dim maxIterations As Integer
    
    xLeft = x1
    xRight = x2
    maxIterations = 100
    iterations = 0
    
    ' Проверка наличия корня
    fLeft = F07(xLeft, A, B)
    fRight = F07(xRight, A, B)
    
    If fLeft * fRight > 0 Then
        NaytiKoren = CVErr(xlErrNA) ' Корня нет
        Exit Function
    End If
    
    ' Метод бисекции
    Do While (xRight - xLeft) > tochnost And iterations < maxIterations
        xMid = (xLeft + xRight) / 2
        fMid = F07(xMid, A, B)
        
        If Abs(fMid) < tochnost Then
            NaytiKoren = xMid
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
    
    NaytiKoren = (xLeft + xRight) / 2
End Function

' Поиск подходящих коэффициентов A и B
Sub NaytiKoefitsienty()
    Dim x1 As Double, x2 As Double
    Dim A As Double, B As Double
    Dim A_min As Double, A_max As Double, A_step As Double
    Dim B_min As Double, B_max As Double, B_step As Double
    Dim found As Boolean
    Dim koren As Double
    Dim row As Integer
    
    ' Параметры интервала (из ячеек или задать вручную)
    x1 = Range("B1").Value ' Начало интервала
    x2 = Range("B2").Value ' Конец интервала
    
    ' Диапазоны поиска коэффициентов
    A_min = Range("B3").Value ' Минимальное A
    A_max = Range("B4").Value ' Максимальное A
    A_step = Range("B5").Value ' Шаг для A
    
    B_min = Range("B6").Value ' Минимальное B
    B_max = Range("B7").Value ' Максимальное B
    B_step = Range("B8").Value ' Шаг для B
    
    ' Очистка результатов
    Range("D1:F1000").Clear
    
    ' Заголовки
    Range("D1").Value = "A"
    Range("E1").Value = "B"
    Range("F1").Value = "Koren"
    
    row = 2
    found = False
    
    ' Перебор значений A и B
    A = A_min
    Do While A <= A_max
        B = B_min
        Do While B <= B_max
            If EstKoren(x1, x2, A, B) Then
                koren = NaytiKoren(x1, x2, A, B)
                If Not IsError(koren) Then
                    Range("D" & row).Value = A
                    Range("E" & row).Value = B
                    Range("F" & row).Value = koren
                    row = row + 1
                    found = True
                End If
            End If
            B = B + B_step
        Loop
        A = A + A_step
    Loop
    
    If found Then
        MsgBox "Naydeny koefitsienty! Rezultaty v stolbtsah D-F", vbInformation
    Else
        MsgBox "Koefitsienty ne naydeny. Poprobuyte rasshirit diapazony poiska.", vbExclamation
    End If
End Sub

' ИНСТРУКЦИЯ:
' 1. Создайте таблицу в Excel:
'    A1: x1 (начало интервала)
'    B1: 0.1
'    A2: x2 (конец интервала)
'    B2: 10
'    A3: A_min
'    B3: -5
'    A4: A_max
'    B4: 5
'    A5: A_step
'    B5: 0.5
'    A6: B_min
'    B6: -5
'    A7: B_max
'    B7: 5
'    A8: B_step
'    B8: 0.5
'
' 2. Запустите макрос NaytiKoefitsienty()
' 3. Результаты появятся в столбцах D-F
