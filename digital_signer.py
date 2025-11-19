from ironpdf import *
import hashlib
import tempfile
import os

# Configurar licencia
License.LicenseKey = (
    "IRONSUITE.20213TN098.UTEZ.EDU.MX.14475-"
    "15FB8A0666-BZX763W56D3VDPDV-PNC3F2S7Z6XG-33NUP2VGSLTN-S3LKJZEBSOZW-"
    "XCMY72XBRTRP-JPRLRMZQAI5Y-W5LHUT-T6JY6NFJCA6QUA-DEPLOYMENT.TRIAL-"
    "QJIF47.TRIAL.EXPIRES.19.DEC.2025"
)

# Establecer carpeta temporal adecuada
#Installation.TempFolderPath = os.path.join("dependencies", "ironpdf_temp")


class DigitalSigner:

    def sign_pdf(self, input_pdf: str, output_pdf: str, pfx_path: str, pfx_password: str):
        """
        Firma un archivo PDF usando IronPDF.
        """
        pdf = PdfDocument.FromFile(input_pdf)

        signature = PdfSignature(
            pfx_path,
            pfx_password
        )

        pdf.Sign(signature)
        pdf.SaveAs(output_pdf)


    def sign_txt(self, txt_path: str, output_pdf: str, pfx_path: str, pfx_password: str):
        """
        Convierte un TXT a PDF y lo firma.
        """
        with open(txt_path, "r", encoding="utf-8") as f:
            text = f.read()

        renderer = ChromePdfRenderer()
        pdf = renderer.RenderHtmlAsPdf(f"<pre>{text}</pre>")

        # Crear archivo temporal seguro
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            temp_pdf = tmp.name

        pdf.SaveAs(temp_pdf)

        self.sign_pdf(temp_pdf, output_pdf, pfx_path, pfx_password)

        os.remove(temp_pdf)


    def sign_zip(self, zip_path: str, output_pdf: str, pfx_path: str, pfx_password: str):
        """
        Genera un PDF que contiene el hash del ZIP, y lo firma.
        """
        with open(zip_path, "rb") as f:
            data = f.read()

        sha256_hash = hashlib.sha256(data).hexdigest()

        html = f"""
        <h1>Firma Digital del Archivo ZIP</h1>
        <p><b>Archivo:</b> {os.path.basename(zip_path)}</p>
        <p><b>Hash SHA-256:</b></p>
        <pre>{sha256_hash}</pre>
        """

        renderer = ChromePdfRenderer()
        pdf = renderer.RenderHtmlAsPdf(html)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            temp_pdf = tmp.name

        pdf.SaveAs(temp_pdf)

        self.sign_pdf(temp_pdf, output_pdf, pfx_path, pfx_password)

        os.remove(temp_pdf)
