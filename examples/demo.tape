Output examples/demo.gif

Set Shell "zsh"
Set FontSize 16
Set Width 1100
Set Height 720
Set Padding 20
Set Theme "Catppuccin Mocha"
Set TypingSpeed 35ms

# Move into the fixtures dir and clear any prior outputs
Hide
Type "cd ~/shannon/examples && rm -f clip.mp3 photo.webp notes.docx scan.txt *.jpg && clear"
Enter
Show

Type "shannon --doctor"
Sleep 400ms
Enter
Sleep 2500ms

Type "clear"
Enter
Sleep 200ms

Type "shannon clip.mp4 mp3"
Sleep 400ms
Enter
Sleep 1500ms

Type "shannon photo.png webp"
Sleep 400ms
Enter
Sleep 1500ms

Type "shannon notes.md docx"
Sleep 400ms
Enter
Sleep 1500ms

Type "shannon scan.png txt && cat scan.txt"
Sleep 400ms
Enter
Sleep 2000ms

Type "shannon clip.mp4 gif --duration 1.5 --quality high"
Sleep 400ms
Enter
Sleep 2500ms

Type "ls"
Sleep 400ms
Enter
Sleep 3000ms
