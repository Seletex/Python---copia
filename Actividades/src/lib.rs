use pyo3::prelude::*;
use pyo3::types::PyDict;
use std::collections::HashMap;
use std::time::Instant;

/// Estructura para caching de datos optimizado
#[pyclass]
struct CacheManager {
    data: HashMap<String, (Vec<HashMap<String, String>>, Instant)>,
    ttl_seconds: u64,
}

#[pymethods]
impl CacheManager {
    #[new]
    fn new(ttl_seconds: u64) -> Self {
        CacheManager {
            data: HashMap::new(),
            ttl_seconds,
        }
    }

    /// Obtiene datos del cache si están válidos
    fn get(&self, key: &str) -> Option<Vec<HashMap<String, String>>> {
        self.data.get(key).and_then(|(data, timestamp)| {
            if timestamp.elapsed().as_secs() < self.ttl_seconds {
                Some(data.clone())
            } else {
                None
            }
        })
    }

    /// Guarda datos en el cache
    fn set(&mut self, key: String, value: Vec<HashMap<String, String>>) {
        self.data.insert(key, (value, Instant::now()));
    }

    /// Limpia el cache expirado
    fn cleanup(&mut self) {
        let now = Instant::now();
        self.data.retain(|_, (_, timestamp)| {
            now.duration_since(*timestamp).as_secs() < self.ttl_seconds
        });
    }

    /// Limpia todo el cache
    fn clear(&mut self) {
        self.data.clear();
    }
}

/// Filtrado optimizado de registros
#[pyfunction]
fn filtrar_registros(
    registros: Vec<HashMap<String, String>>,
    filtros: HashMap<String, String>,
) -> PyResult<Vec<HashMap<String, String>>> {
    let start_time = Instant::now();
    
    let mut resultados = Vec::new();
    
    for registro in registros {
        let mut coincide = true;
        
        for (campo, valor_buscado) in &filtros {
            if let Some(valor_registro) = registro.get(campo) {
                if !valor_registro.to_lowercase().contains(&valor_buscado.to_lowercase()) {
                    coincide = false;
                    break;
                }
            } else {
                coincide = false;
                break;
            }
        }
        
        if coincide {
            resultados.push(registro);
        }
    }
    
    let duration = start_time.elapsed();
    println!("Filtrado completado en {:?} - {} resultados", duration, resultados.len());
    
    Ok(resultados)
}

/// Búsqueda optimizada con múltiples criterios
#[pyfunction]
fn buscar_registros_avanzado(
    registros: Vec<HashMap<String, String>>,
    termino: String,
    campos: Vec<String>,
) -> PyResult<Vec<HashMap<String, String>>> {
    let termino_lower = termino.to_lowercase();
    let mut resultados = Vec::new();
    
    for registro in registros {
        for campo in &campos {
            if let Some(valor) = registro.get(campo) {
                if valor.to_lowercase().contains(&termino_lower) {
                    resultados.push(registro.clone());
                    break;
                }
            }
        }
    }
    
    Ok(resultados)
}

/// Estadísticas rápidas de registros
#[pyfunction]
fn calcular_estadisticas(
    registros: Vec<HashMap<String, String>>,
    campo: String,
) -> PyResult<HashMap<String, usize>> {
    let mut estadisticas = HashMap::new();
    
    for registro in registros {
        if let Some(valor) = registro.get(&campo) {
            *estadisticas.entry(valor.clone()).or_insert(0) += 1;
        }
    }
    
    Ok(estadisticas)
}

/// Ordenamiento optimizado
#[pyfunction]
fn ordenar_registros(
    mut registros: Vec<HashMap<String, String>>,
    campo: String,
    ascendente: bool,
) -> PyResult<Vec<HashMap<String, String>>> {
    let campo_clone = campo.clone();
    
    registros.sort_by(|a, b| {
        let valor_a = a.get(&campo_clone).map(|s| s.as_str()).unwrap_or("");
        let valor_b = b.get(&campo_clone).map(|s| s.as_str()).unwrap_or("");
        
        if ascendente {
            valor_a.cmp(valor_b)
        } else {
            valor_b.cmp(valor_a)
        }
    });
    
    Ok(registros)
}

/// Registro de módulo Python
#[pymodule]
fn actividades_rust(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<CacheManager>()?;
    m.add_function(wrap_pyfunction!(filtrar_registros, m)?)?;
    m.add_function(wrap_pyfunction!(buscar_registros_avanzado, m)?)?;
    m.add_function(wrap_pyfunction!(calcular_estadisticas, m)?)?;
    m.add_function(wrap_pyfunction!(ordenar_registros, m)?)?;
    
    Ok(())
}