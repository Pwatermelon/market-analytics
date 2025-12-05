REM КОНТРОЛЬНОЕ ЗАДАНИЕ 3 - LIBREOFFICE CALC
REM Вариант 7: Вычисление площади и углов ромба по его диагоналям
REM Макрос для LibreOffice Calc

Sub VychislitParametriRomb
    REM Макрос для вычисления параметров ромба
    REM Получаем значения диагоналей из ячеек
    Dim d1 As Double
    Dim d2 As Double
    Dim ploshad As Double
    Dim ugolAlfa As Double
    Dim ugolBeta As Double
    Dim storona As Double
    Dim perimetr As Double
    Const PI As Double = 3.14159265358979
    
    Dim oSheet As Object
    oSheet = ThisComponent.getSheets().getByIndex(0)
    
    REM Читаем значения из ячеек B1 и B2
    d1 = oSheet.getCellByPosition(1, 0).getValue()
    d2 = oSheet.getCellByPosition(1, 1).getValue()
    
    REM Вычисляем параметры
    ploshad = (d1 * d2) / 2
    ugolAlfa = 2 * Atn(d2 / d1) * 180 / PI
    ugolBeta = 180 - ugolAlfa
    storona = Sqr((d1 / 2) ^ 2 + (d2 / 2) ^ 2)
    perimetr = 4 * storona
    
    REM Записываем результаты в ячейки
    oSheet.getCellByPosition(1, 2).setValue(ploshad)
    oSheet.getCellByPosition(1, 3).setValue(ugolAlfa)
    oSheet.getCellByPosition(1, 4).setValue(ugolBeta)
    oSheet.getCellByPosition(1, 5).setValue(storona)
    oSheet.getCellByPosition(1, 6).setValue(perimetr)
    
    REM Форматируем результаты
    oSheet.getCellByPosition(1, 2).setPropertyValue("NumberFormat", 2)
    oSheet.getCellByPosition(1, 3).setPropertyValue("NumberFormat", 2)
    oSheet.getCellByPosition(1, 4).setPropertyValue("NumberFormat", 2)
    oSheet.getCellByPosition(1, 5).setPropertyValue("NumberFormat", 2)
    oSheet.getCellByPosition(1, 6).setPropertyValue("NumberFormat", 2)
    
    REM Добавляем единицы измерения
    oSheet.getCellByPosition(2, 2).setString("ед²")
    oSheet.getCellByPosition(2, 3).setString("°")
    oSheet.getCellByPosition(2, 4).setString("°")
    oSheet.getCellByPosition(2, 5).setString("ед")
    oSheet.getCellByPosition(2, 6).setString("ед")
    
    MsgBox "Parametry romba vychisleny!", 0, "Gotovo"
End Sub



