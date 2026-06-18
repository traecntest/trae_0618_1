import os
from pathlib import Path

template_dir = Path("resources/templates")

for template_file in template_dir.glob("*"):
    if template_file.is_file():
        content = template_file.read_text(encoding="utf-8")
        
        # 替换 Jinja2 分隔符
        # 先替换 {% %} 为 <%% %%>
        content = content.replace("{%", "<%%")
        content = content.replace("%}", "%%>")
        # 再替换 {{ }} 为 <% %>
        content = content.replace("{{", "<%")
        content = content.replace("}}", "%>")
        
        template_file.write_text(content, encoding="utf-8")
        print(f"已更新: {template_file}")

print("所有模板文件已更新完成！")
