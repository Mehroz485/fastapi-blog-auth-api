from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from database import engine, SessionLocal

import model, schemas
import auth  # FIX: import the auth router so its routes get registered below

model.Base.metadata.create_all(bind=engine)

app = FastAPI()


def get_db():
    db = SessionLocal()
    # FIX: original code had inconsistent/broken indentation here
    # (try/finally lines were over-indented and didn't line up,
    # which is a SyntaxError/IndentationError in Python).
    try:
        yield db
    finally:
        db.close()


# FIX: auth.py's routes depend on get_db and the app instance, so we
# include its router here, after both exist.
app.include_router(auth.router)


@app.get("/")
def home():
    return {
        "message": "Welcome"
    }


# FIX: decorator line ended with ":" instead of nothing (route decorators
# are not followed by a colon-block like an if/for statement) — removed it.
@app.post("/blogs", response_model=schemas.BlogResponse)
def create_blog(blog: schemas.BlogCreate, db: Session = Depends(get_db)):
    new_blog = model.Blog(  # FIX: was "models.Blog" - no module called "models" exists, only "model"
        title=blog.title,
        content=blog.content  # FIX: missing comma after blog.title caused a SyntaxError
    )
    db.add(new_blog)
    db.commit()
    db.refresh(new_blog)

    return new_blog


# FIX: removed trailing colon after the decorator (same issue as above).
# FIX: renamed function from "gt_blogs" to "get_blogs" - it was reused as the
# function name for 4 different routes, and since Python functions live in
# the same namespace, each later definition silently overwrote the earlier
# one, breaking those routes.
@app.get("/blogs", response_model=list[schemas.BlogResponse])
def get_blogs(db: Session = Depends(get_db)):
    return db.query(model.Blog).all()  # FIX: ".all" was missing call parentheses


@app.get("/blogs/{id}", response_model=schemas.BlogResponse)  # FIX: was list[...] but this returns a single blog, not a list
def get_blog(id: int, db: Session = Depends(get_db)):
    blog = db.query(model.Blog).filter(model.Blog.id == id).first()

    if not blog:
        # FIX: HTTPException must be "raised", not just called as an
        # expression, or the function continues running and returns
        # "blog" (which is None) instead of stopping with an error.
        # FIX: status_code should be an int (404), not the string "400",
        # and 404 is the correct semantic code for "not found".
        raise HTTPException(status_code=404, detail="Not found")

    return blog


@app.put("/blogs/{id}", response_model=schemas.BlogResponse)
def update_blog(id: int, blog: schemas.BlogCreate, db: Session = Depends(get_db)):  # FIX: renamed from "gt_blogs" (duplicate name)
    existing_blog = db.query(model.Blog).filter(model.Blog.id == id).first()
    if not existing_blog:
        raise HTTPException(status_code=404, detail="Not found")  # FIX: same raise/int-status fix as above

    existing_blog.title = blog.title
    existing_blog.content = blog.content

    db.commit()
    return existing_blog


# FIX: this was "app.put(...)" used for a DELETE operation, missing the
# "@" decorator symbol entirely, and missing ":" -> "()" already covered,
# but more importantly it used the wrong HTTP verb. Changed to @app.delete.
@app.delete("/blogs/{id}")
def delete_blog(id: int, db: Session = Depends(get_db)):  # FIX: renamed from "gt_blogs" (duplicate name)
    existing_blog = db.query(model.Blog).filter(model.Blog.id == id).first()
    if not existing_blog:
        raise HTTPException(status_code=404, detail="Not found")

    db.delete(existing_blog)  # FIX: was "blog.delete()" - "blog" doesn't exist in this
    # function's scope (it's existing_blog here), and the SQLAlchemy
    # pattern is db.delete(obj), not obj.delete().
    db.commit()

    return {
        "message": "blog deleted successfully"  # FIX: typo "bog" -> "blog"
    }
