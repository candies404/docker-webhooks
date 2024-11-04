class ProjectService:
    def __init__(self, project_config):
        self.project_config = project_config

    def is_valid_project(self, project):
        """检查项目是否有效"""
        return project in self.project_config

    def get_project_config(self, project):
        """获取项目配置"""
        return self.project_config.get(project, {})
