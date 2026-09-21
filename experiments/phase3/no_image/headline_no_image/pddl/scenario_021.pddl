(define (problem head_into_cooking_area)
  (:domain household)

  (:objects
    kitchen - location
    living_room - location
  )

  (:init
    (robot-at living_room)
    (connected living_room kitchen)
  )

  (:goal
    (robot-at kitchen)
  )
)