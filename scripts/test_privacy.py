#!/usr/bin/env python3
"""Test de privacidad: genera SVG con campo 'user' y verifica que no se muestre en la salida."""
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.svg_generator import SVGGenerator


def test_privacy_hide_user():
    svg_gen = SVGGenerator()
    session = {
        'title': 'Prueba Privacidad',
        'artist': 'Artista',
        'album': 'Álbum',
        'user': 'UsuarioSecreto'
    }
    svg = svg_gen.generate_now_playing_svg(session)
    # Verificaciones
    assert 'Usuario' not in svg, "La palabra 'Usuario' no debe aparecer en el SVG"
    assert 'UsuarioSecreto' not in svg, "El nombre de usuario no debe aparecer en el SVG"
    print('✅ Test privacy passed')


if __name__ == '__main__':
    try:
        test_privacy_hide_user()
        sys.exit(0)
    except AssertionError as e:
        print('❌', e)
        sys.exit(1)
