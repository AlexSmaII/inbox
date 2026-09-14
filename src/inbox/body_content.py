EMAIL_FRONTMATTER = """
<html>
  <head>
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
    <style type="text/css" style="display:none">
      <!--
      p {
        margin-top: 0;
        margin-bottom: 0
      }
      -->
    </style>
  </head>
  <body dir="ltr">
"""

EMAIL_ENDMATTER = """
    <br/>
    <br/>
    <div style="border:1px dotted #003333; padding:.8em">
      <p/>
      <span style="font-size:9pt; font-family:'Cambria','times new roman','garamond',serif; color:#ff0000">LEGAL NOTICE </span>
      <br/>
      <p style="font-size:8pt; line-height:10pt; font-family:'Cambria','times roman',serif">This message including any attachments contains confidential information intended for a specific individual and purpose, and is protected by law. If you are not the intended recipient, you should delete this message. Any disclosure, copying, or distribuition of this message, or the taking of any action based on it, is strictly prohibited. </p>
      <span style="padding-top:10px; font-weight:bold; color:#CC0000; font-size:10pt; font-family:'Calibri',Arial,sans-serif">
        <a href="http://www.natrio.com">NATRIO.COM</a>
      </span>
      <br/>
    </div>
  </body>
</html>
"""

def generate_email_html(
    text : str
) -> str:
    paragraphs = text.split("\n")
    paragraphs = [f'<div style="font-family:\'Figtree Medium\',Aptos,Aptos_EmbeddedFont,Aptos_MSFontService,Calibri,Helvetica,sans-serif; font-size:12pt; color:#000">{p}</div><br/>' for p in paragraphs]
    paragraphs = "\n\t\t".join(paragraphs)

    return EMAIL_FRONTMATTER + paragraphs + EMAIL_ENDMATTER