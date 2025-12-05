' КОНТРОЛЬНОЕ ЗАДАНИЕ 2 (версия с латинскими именами)
' Вариант 7: Вычисление площади и углов ромба по его диагоналям
' Функции пользователя в стандартном модуле Excel

' Функция вычисления площади ромба
Function PloshadRomb(d1 As Double, d2 As Double) As Double
    ' S = (d1 * d2) / 2
    PloshadRomb = (d1 * d2) / 2
End Function

' Функция вычисления угла α (в градусах)
Function UgolAlfa(d1 As Double, d2 As Double) As Double
    ' α = 2 * arctan(d2/d1) в градусах
    Const PI As Double = 3.14159265358979
    UgolAlfa = 2 * Atn(d2 / d1) * 180 / PI
End Function

' Функция вычисления угла β (в градусах)
Function UgolBeta(d1 As Double, d2 As Double) As Double
    ' β = 180° - α
    UgolBeta = 180 - UgolAlfa(d1, d2)
End Function

' Функция вычисления стороны ромба
Function StoronaRomb(d1 As Double, d2 As Double) As Double
    ' a = √((d1/2)² + (d2/2)²)
    StoronaRomb = Sqr((d1 / 2) ^ 2 + (d2 / 2) ^ 2)
End Function

' Функция вычисления периметра ромба
Function PerimetrRomb(d1 As Double, d2 As Double) As Double
    ' P = 4a
    PerimetrRomb = 4 * StoronaRomb(d1, d2)
End Function

' Функция вычисления всех параметров ромба (возвращает массив)
Function ParametriRomb(d1 As Double, d2 As Double) As Variant
    Dim result(1 To 5) As Double
    result(1) = PloshadRomb(d1, d2)
    result(2) = UgolAlfa(d1, d2)
    result(3) = UgolBeta(d1, d2)
    result(4) = StoronaRomb(d1, d2)
    result(5) = PerimetrRomb(d1, d2)
    ParametriRomb = result
End Function

' ИНСТРУКЦИЯ ПО ИСПОЛЬЗОВАНИЮ:
' 1. Откройте Excel
' 2. Нажмите Alt+F11 для открытия редактора VBA
' 3. Вставьте → Модуль
' 4. Скопируйте этот код в модуль
' 5. Вернитесь в Excel и используйте функции:
'    =PloshadRomb(10;8)
'    =UgolAlfa(10;8)
'    =UgolBeta(10;8)
'    =StoronaRomb(10;8)
'    =PerimetrRomb(10;8)



