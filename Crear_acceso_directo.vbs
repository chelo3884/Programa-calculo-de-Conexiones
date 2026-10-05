' Crea el icono "Conexiones Metálicas" en el Escritorio y en el menú Inicio (doble clic en este archivo).
' El acceso directo abre el programa SIN ventana de consola.
Option Explicit
Dim sh, fso, aqui, escritorio, inicio, destino, lnk, lista, i, ruta
Set sh = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
aqui = fso.GetParentFolderName(WScript.ScriptFullName)
destino = aqui & "\Iniciar.pyw"
If Not fso.FileExists(destino) Then
  MsgBox "No se encontró Iniciar.pyw junto a este archivo." & vbCrLf & "Descomprima toda la carpeta antes de crear el acceso directo.", 16, "Conexiones metálicas"
  WScript.Quit 1
End If
escritorio = sh.SpecialFolders("Desktop")
inicio = sh.SpecialFolders("Programs")
lista = Array(escritorio, inicio)
For i = 0 To 1
  ruta = lista(i) & "\Conexiones Metálicas.lnk"
  Set lnk = sh.CreateShortcut(ruta)
  lnk.TargetPath = destino
  lnk.WorkingDirectory = aqui
  lnk.IconLocation = aqui & "\assets\icono.ico"
  lnk.Description = "Diseño de conexiones metálicas (AISC)"
  lnk.WindowStyle = 1
  lnk.Save
Next
MsgBox "Listo. Se creó el icono ""Conexiones Metálicas"" en el Escritorio y en el menú Inicio." & vbCrLf & vbCrLf & "Si al hacer doble clic no abre, instale Python (python.org, marcando ""Add Python to PATH"").", 64, "Conexiones metálicas"
