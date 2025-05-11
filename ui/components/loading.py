import flet as ft

class LoadingAnimation(ft.Container):
    def __init__(self):
        super().__init__()
        self.expand = True
        self.visible = False
        self.bgcolor = ft.Colors.with_opacity(0.5, ft.Colors.BLACK)
        self.padding = ft.padding.all(0)
        self.alignment = ft.Alignment.center

        self.spinner = ft.Container(
            content=ft.Icon(
                name=ft.Icons.AUTORENEW_ROUNDED,
                size=40,
                color=ft.Colors.PRIMARY,
            ),
            animate_rotation=ft.Animation(
                duration=1500,
                curve=ft.AnimationCurve.LINEAR,
            ),
            rotate=ft.Rotate(0, alignment=ft.Alignment.center),
        )

        self.text = ft.Container(
            content=ft.Text(
                value="Loading...",
                size=16,
                color=ft.Colors.ON_SURFACE_VARIANT,
                weight="w500",
            ),
            animate_scale=ft.Animation(
                duration=1000,
                curve=ft.AnimationCurve.EASE_IN_OUT,
            ),
            scale=ft.Scale(1),
        )

        self.shimmer = ft.Container(
            width=200,
            height=4,
            border_radius=2,
            gradient=ft.LinearGradient(
                begin=ft.Alignment.center_left,
                end=ft.Alignment.center_right,
                colors=[
                    ft.Colors.with_opacity(0.1, ft.Colors.PRIMARY),
                    ft.Colors.with_opacity(0.3, ft.Colors.PRIMARY),
                    ft.Colors.with_opacity(0.1, ft.Colors.PRIMARY),
                ],
            ),
            animate_position=ft.Animation(
                duration=1500,
                curve=ft.AnimationCurve.EASE_IN_OUT,
            ),
        )

        inner_container = ft.Container(
            content=ft.Column(
                controls=[
                    self.spinner,
                    self.text,
                    self.shimmer,
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=20,
            ),
            bgcolor=ft.Colors.with_opacity(0.95, ft.Colors.BLACK54),
            padding=ft.padding.all(40),
            border_radius=12,
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=8,
                color=ft.Colors.with_opacity(0.1, ft.Colors.SHADOW),
                offset=ft.Offset(0, 2),
            ),
        )

        self.content = ft.Stack(
            controls=[
                ft.Container(
                    content=inner_container,
                    alignment=ft.Alignment.center,
                    expand=True,
                ),
            ],
        )

    def did_mount(self):
        """Start animations when component mounts"""
        self.spinner.rotate.angle = 360
        self.spinner.update()

        self.text.scale = ft.Scale(0.95)
        self.text.update()

        self.shimmer.left = -200
        self.shimmer.update()

    def will_unmount(self):
        """Stop animations when component unmounts"""
        self.spinner.rotate.angle = 0
        self.text.scale = ft.Scale(1)
        self.shimmer.left = 0

    @property
    def value(self) -> str:
        """Get the current text value"""
        return self.text.content.value

    @value.setter
    def value(self, val: str):
        """Set the text value"""
        self.text.content.value = val
