
import unittest
import sys
import os

# Agregar path
sys.path.append(os.path.join(os.getcwd(), 'Actividades'))

from Actividades.app import app
from Actividades.database import cargar_actividades_globales, guardar_actividades

class FlaskTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        self.test_activity = "ACTIVIDAD_TEST_FLASK"

    def tearDown(self):
        # Limpiar
        act = cargar_actividades_globales()
        if self.test_activity in act:
            act.remove(self.test_activity)
            guardar_actividades(act)

    def test_index_redirect(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        # Debe mostrar login
        self.assertIn(b'Inciar Sesion', response.data) # Typo in original template? Checking content loosely
        # Or check for input name="usuario"
        self.assertIn(b'name="usuario"', response.data)

    def test_login_flow(self):
        # Login
        response = self.client.post('/login', data={'usuario': 'admin'}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Bienvenido, admin', response.data)
        
        # Access protected route
        response = self.client.get('/gestion')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Actividades Globales', response.data)
        
        # Add global activity
        response = self.client.post('/agregar_actividad_global', 
                                    data={'nuevo_item': self.test_activity},
                                    follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Actividad agregada', response.data)
        
        # Verify in DB
        act = cargar_actividades_globales()
        self.assertIn(self.test_activity, act)

if __name__ == '__main__':
    unittest.main()
