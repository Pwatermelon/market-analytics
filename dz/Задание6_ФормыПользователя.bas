' КОНТРОЛЬНОЕ ЗАДАНИЕ 6
' Вариант 7: Вычисление площади и углов ромба по его диагоналям
' Реализация с использованием форм пользователя (UserForm)

' Создание формы пользователя:
' 1. Alt+F11 → Вставка → UserForm
' 2. Добавьте элементы:
'    - Label1: "Диагональ 1:"
'    - TextBox1: для ввода d1
'    - Label2: "Диагональ 2:"
'    - TextBox2: для ввода d2
'    - Label3: "Площадь:"
'    - Label4: "Угол α:"
'    - Label5: "Угол β:"
'    - Label6: "Сторона:"
'    - Label7: "Периметр:"
'    - TextBox3-7: для вывода результатов
'    - CommandButton1: "Вычислить"
'    - CommandButton2: "Очистить"
'    - CommandButton3: "Выход"

' Код для формы пользователя:

Private Sub CommandButton1_Click()
    ' Кнопка "Вычислить"
    Dim d1 As Double, d2 As Double
    Dim ploshad As Double, ugolAlfa As Double, ugolBeta As Double
    Dim storona As Double, perimetr As Double
    Const PI As Double = 3.14159265358979
    
    ' Проверка ввода
    If TextBox1.Value = "" Or TextBox2.Value = "" Then
        MsgBox "Vvedite znacheniya diagonaley!", vbExclamation
        Exit Sub
    End If
    
    On Error GoTo Oshibka
    d1 = CDbl(TextBox1.Value)
    d2 = CDbl(TextBox2.Value)
    
    If d1 <= 0 Or d2 <= 0 Then
        MsgBox "Diagonali dolzhny byt polozhitelnymi chislami!", vbExclamation
        Exit Sub
    End If
    
    ' Вычисления
    ploshad = (d1 * d2) / 2
    ugolAlfa = 2 * Atn(d2 / d1) * 180 / PI
    ugolBeta = 180 - ugolAlfa
    storona = Sqr((d1 / 2) ^ 2 + (d2 / 2) ^ 2)
    perimetr = 4 * storona
    
    ' Вывод результатов
    TextBox3.Value = Format(ploshad, "0.00")
    TextBox4.Value = Format(ugolAlfa, "0.00") & "°"
    TextBox5.Value = Format(ugolBeta, "0.00") & "°"
    TextBox6.Value = Format(storona, "0.00")
    TextBox7.Value = Format(perimetr, "0.00")
    
    Exit Sub
    
Oshibka:
    MsgBox "Oshibka vvoda dannyh! Proverte pravilnost vvedennyh znacheniy.", vbCritical
End Sub

Private Sub CommandButton2_Click()
    ' Кнопка "Очистить"
    TextBox1.Value = ""
    TextBox2.Value = ""
    TextBox3.Value = ""
    TextBox4.Value = ""
    TextBox5.Value = ""
    TextBox6.Value = ""
    TextBox7.Value = ""
    TextBox1.SetFocus
End Sub

Private Sub CommandButton3_Click()
    ' Кнопка "Выход"
    Unload Me
End Sub

Private Sub TextBox1_KeyPress(ByVal KeyAscii As MSForms.ReturnInteger)
    ' Разрешить только цифры, точку и запятую
    If (KeyAscii < 48 Or KeyAscii > 57) And KeyAscii <> 46 And KeyAscii <> 44 And KeyAscii <> 8 Then
        KeyAscii = 0
    End If
End Sub

Private Sub TextBox2_KeyPress(ByVal KeyAscii As MSForms.ReturnInteger)
    ' Разрешить только цифры, точку и запятую
    If (KeyAscii < 48 Or KeyAscii > 57) And KeyAscii <> 46 And KeyAscii <> 44 And KeyAscii <> 8 Then
        KeyAscii = 0
    End If
End Sub

Private Sub UserForm_Initialize()
    ' Инициализация формы
    Me.Caption = "Vychislenie parametrov romba"
    CommandButton1.Caption = "Vychislit"
    CommandButton2.Caption = "Ochistit"
    CommandButton3.Caption = "Vyhod"
End Sub

' МАКРОС ДЛЯ ЗАПУСКА ФОРМЫ:
Sub PokazatFormuRomb()
    UserForm1.Show
End Sub

' ИНСТРУКЦИЯ:
' 1. Alt+F11 → Вставка → UserForm
' 2. Создайте форму с элементами управления
' 3. Двойной клик по форме → вставьте код выше
' 4. Сохраните и закройте редактор VBA
' 5. Создайте кнопку на листе или запустите макрос PokazatFormuRomb()
