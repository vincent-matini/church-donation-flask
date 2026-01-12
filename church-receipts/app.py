from flask import Flask, render_template, request

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        name = request.form.get("name")
        donation_type = request.form.get("type")
        amount = request.form.get("amount")

        return render_template(
            "receipt.html",
            name=name,
            donation_type=donation_type,
            amount=amount
        )

    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True)
