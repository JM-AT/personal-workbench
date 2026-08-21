use std::path::PathBuf;
use tauri::Manager;

/// 在打包后或开发态下，定位本地 Python 后端 app.py 的若干候选路径。
fn backend_candidates(app: &tauri::AppHandle) -> Vec<PathBuf> {
    let mut v = Vec::new();
    if let Ok(r) = app.path().resource_dir() {
        v.push(r.join("backend").join("app.py"));
    }
    if let Ok(exe) = std::env::current_exe() {
        if let Some(parent) = exe.parent() {
            v.push(parent.join("backend").join("app.py"));
            v.push(parent.join("..").join("backend").join("app.py"));
            v.push(parent.join("..").join("..").join("backend").join("app.py"));
        }
    }
    v.push(PathBuf::from("backend/app.py"));
    v
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
fn main() {
    tauri::Builder::default()
        .setup(|app| {
            // 最佳努力启动本地后端；失败不阻塞界面（用户可在设置中看到不可用）。
            for c in backend_candidates(app) {
                if c.exists() {
                    let _ = std::process::Command::new("python").arg(&c).spawn();
                    break;
                }
            }
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
