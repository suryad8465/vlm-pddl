(define (problem bring_mug_to_living_room)
  (:domain household)

  (:objects
    kitchen - location
    living_room - location
    table - object
    mug - object
  )

  (:init
    (robot-at kitchen)
    (connected kitchen living_room)
    (connected living_room kitchen)

    (located table kitchen)
    (located mug table)
    (on mug table)
    (manipulable mug)
  )

  (:goal
    (located mug living_room)
  )
)