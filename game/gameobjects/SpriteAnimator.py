import pyasge


class SpriteAnimator:

    def __init__(self, sprite, td):
        """ The animator once called in update will handle everything, but to do so
            it needs specific values, in order:
            - Sprite: reference of the sprite to be animated
            - Texture: file path of the texture we have to use
            - Starting_x: X cord of the top left point of the first sprite
            - Starting_y: Y cord of the top left point of the first sprite
            - Width: width of the single sprite bounding box
            - Height: height on the single sprite bounding box
            - Gap: gap between each sprite, first one doesn't need to have one
            - Frames: total frames of the animation
            - Middle: Middle point of the animation, where idle and run differ

            dt is a sub-dictionary of the texture dictionary of dictionaries that
            contains the info needed to grab the samples.
            """
        self.spriteSheet = sprite
        self.spriteSheet.loadTexture(td["filepath"])
        self.spriteSheet.scale = td["scale"]
        self.numberOfFrames = td["frames"]
        self.current_frame = 0
        self.timer = 0
        self.middle_point = td["middle"]
        self.sprite_cords = []

        self.frame_change_time = td["frame_interval"]

        # Sets how big the sprite is going to be
        # Leave it as 16x16 for best stability
        self.spriteSheet.width = td["width"]
        self.spriteSheet.height = td["height"]

        # Generates all the frames for the desired animation
        for i in range(0, td["frames"]):
            self.sprite_cords.append([td["start_x"] + (td["width"] * i) + (td["gap"] * i), td["start_y"], td["width"], td["height"]])

        self.changeFocus(0)

    def animateSprite(self, game_time: pyasge.GameTime, animation_state):
        self.timer += game_time.fixed_timestep

        if self.timer > self.frame_change_time:
            self.timer = 0

            # Takes the segments before the middle point. they are supposed to be the idle anim.
            if animation_state == 0:
                self.current_frame += 1
                if self.current_frame > self.middle_point - 1:
                    self.current_frame = 0
                self.changeFocus(self.current_frame)

            # Takes the other segments after the middle point, they are supposed to be the run anim.
            elif animation_state == 1:
                self.current_frame += 1
                if self.current_frame > (self.middle_point*2) - 1 or self.current_frame < self.middle_point:
                    self.current_frame = self.middle_point
                self.changeFocus(self.current_frame)

            # Runs through the animation once and stops at final frame
            elif animation_state == 2:
                if self.current_frame != self.middle_point - 1:
                    self.current_frame += 1
                    self.changeFocus(self.current_frame)

            # In the current tile sheet an eventual 9th frame would be a jump
            else:
                pass

    def resetAnimation(self):
        self.current_frame = 0
        self.changeFocus(0)

    def changeFocus(self, frame):
        # Sets the current texture to the coordinates
        self.spriteSheet.src_rect[pyasge.Sprite.SourceRectIndex.START_X] = self.sprite_cords[frame][0]
        self.spriteSheet.src_rect[pyasge.Sprite.SourceRectIndex.START_Y] = self.sprite_cords[frame][1]
        self.spriteSheet.src_rect[pyasge.Sprite.SourceRectIndex.LENGTH_X] = self.sprite_cords[frame][2]
        self.spriteSheet.src_rect[pyasge.Sprite.SourceRectIndex.LENGTH_Y] = self.sprite_cords[frame][3]
