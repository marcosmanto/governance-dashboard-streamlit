def reset_password_template(reset_link: str) -> str:
    return f"""
    <html>
        <body style="font-family: Arial, sans-serif; background-color: #f4f6f8; padding: 20px;">
            <div style="max-width: 600px; margin: auto; background: white; padding: 30px; border-radius: 8px;">
                <h2 style="color: #1f2937;">Redefinição de Senha</h2>
                <p>Você solicitou a redefinição de sua senha.</p>
                <p>Clique no botão abaixo:</p>

                <a href="{reset_link}"
                   style="display: inline-block; padding: 12px 20px; background-color: #2563eb; color: white; text-decoration: none; border-radius: 6px;">
                   Redefinir Senha
                </a>

                <p style="margin-top: 20px; font-size: 12px; color: #6b7280;">
                    Este link expira em 30 minutos.
                </p>
            </div>
        </body>
    </html>
    """
