(define (problem go_to_kitchen)
  (:domain household)

  (:objects
    kitchen - location
  )

  (:init
    (robot-at living_room)
    (connected living_room kitchen)
  )

  (:goal
    (robot-at kitchen)
  )
)