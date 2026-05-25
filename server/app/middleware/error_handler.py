"""Global error handling middleware for FastAPI."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


class AppException(Exception):
    """Base application exception."""

    def __init__(self, code: str, message: str, status_code: int = 400, detail: str = ""):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.detail = detail


# Predefined error types
class InvalidParams(AppException):
    def __init__(self, detail: str = ""):
        super().__init__("INVALID_PARAMS", "请求参数有误", 400, detail)


class InvalidSubjectCount(AppException):
    def __init__(self):
        super().__init__("INVALID_SUBJECT_COUNT", "请选择恰好3门选考科目", 400)


class DuplicateSubjects(AppException):
    def __init__(self):
        super().__init__("DUPLICATE_SUBJECTS", "选考科目不能重复", 400)


class ScoreExceedsMax(AppException):
    def __init__(self):
        super().__init__("SCORE_EXCEEDS_MAX", "得分不能超过满分", 400)


class InvalidMaxScore(AppException):
    def __init__(self):
        super().__init__("INVALID_MAX_SCORE", "满分需在10-300之间", 400)


class GradeRequiresSubjects(AppException):
    def __init__(self):
        super().__init__("GRADE_REQUIRES_SUBJECTS", "高三必须选择等级考科目", 400)


class Unauthorized(AppException):
    def __init__(self):
        super().__init__("UNAUTHORIZED", "请先登录", 401)


class FreeLimitErrorNotes(AppException):
    def __init__(self):
        super().__init__(
            "FREE_LIMIT_ERROR_NOTES",
            "免费版最多保存10道错题，升级解锁无限存储",
            403,
        )


class FreeLimitGrowth(AppException):
    def __init__(self):
        super().__init__(
            "FREE_LIMIT_GROWTH",
            "免费版最多保存5条成长记录，升级解锁无限记录",
            403,
        )


class FreeLimitExams(AppException):
    def __init__(self):
        super().__init__(
            "FREE_LIMIT_EXAMS",
            "免费版最多记录3次考试，升级解锁无限记录",
            403,
        )


class FeatureRequiresStandard(AppException):
    def __init__(self):
        super().__init__(
            "FEATURE_REQUIRES_STANDARD",
            "此功能需要标准版，升级后即可使用",
            403,
        )


class FeatureRequiresPremium(AppException):
    def __init__(self):
        super().__init__(
            "FEATURE_REQUIRES_PREMIUM",
            "此功能需要高级版，升级后即可使用",
            403,
        )


class CannotDeleteSystemMilestone(AppException):
    def __init__(self):
        super().__init__(
            "CANNOT_DELETE_SYSTEM_MILESTONE",
            "系统预置里程碑不可删除",
            403,
        )


class StudentNotFound(AppException):
    def __init__(self):
        super().__init__("STUDENT_NOT_FOUND", "未找到该学生档案", 404)


class ResourceNotFound(AppException):
    def __init__(self):
        super().__init__("RESOURCE_NOT_FOUND", "未找到该资源", 404)


class DuplicateExamDate(AppException):
    def __init__(self):
        super().__init__("DUPLICATE_EXAM_DATE", "该日期已有同名考试记录", 409)


class ImageTooLarge(AppException):
    def __init__(self):
        super().__init__("IMAGE_TOO_LARGE", "图片大小不能超过10MB", 413)


class RateLimitExceeded(AppException):
    def __init__(self):
        super().__init__("RATE_LIMIT_EXCEEDED", "操作太频繁，请稍后再试", 429)


class InternalError(AppException):
    def __init__(self, detail: str = ""):
        super().__init__("INTERNAL_ERROR", "系统繁忙，请稍后再试", 500, detail)


def setup_error_handlers(app: FastAPI) -> None:
    """Register global exception handlers on the FastAPI app."""

    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        content = {"error": {"code": exc.code, "message": exc.message}}
        if exc.detail and request.app.debug:
            content["error"]["detail"] = exc.detail
        return JSONResponse(status_code=exc.status_code, content=content)

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": "HTTP_ERROR",
                    "message": str(exc.detail),
                }
            },
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        content = {"error": {"code": "INTERNAL_ERROR", "message": "系统繁忙，请稍后再试"}}
        if request.app.debug:
            content["error"]["detail"] = str(exc)
        return JSONResponse(status_code=500, content=content)
