from flask import Flask, render_template_string

app = Flask(__name__)

# Template HTML con JavaScript incorporato
template = '''
<!DOCTYPE html>
<html>
<head>
    <title>Cambia Colore Pulsanti</title>
    <style>
        .button {
            padding: 15px 30px;
            margin: 10px;
            font-size: 16px;
            cursor: pointer;
            transition: background-color 0.3s;
        }
    </style>
</head>
<body>
    <h1>Clicca i pulsanti!</h1>
    <button id="btn1" class="button" style="background-color: #ff9999">Pulsante 1</button>
    <button id="btn2" class="button" style="background-color: #99ff99">Pulsante 2</button>
    <button id="btn3" class="button" style="background-color: #9999ff">Pulsante 3</button>

    <script>
        function getRandomColor() {
            var letters = '0123456789ABCDEF';
            var color = '#';
            for (var i = 0; i < 6; i++) {
                color += letters[Math.floor(Math.random() * 16)];
            }
            return color;
        }

        document.getElementById('btn1').onclick = function() {
            this.style.backgroundColor = getRandomColor();
        }
        
        document.getElementById('btn2').onclick = function() {
            this.style.backgroundColor = getRandomColor();
        }
        
        document.getElementById('btn3').onclick = function() {
            this.style.backgroundColor = getRandomColor();
        }
    </script>
</body>
</html>
'''

@app.route('/')
def home():
    return render_template_string(template)

if __name__ == '__main__':
    app.run(debug=True)