(define (problem move_mug_to_living_room)
  (:domain household)

  (:objects
    kitchen living_room - location
    table mug - object
  )

  (:init
    (robot-at kitchen)
    (connected kitchen living_room)
    (connected living_room kitchen)

    (located table kitchen)
    (located mug kitchen)
    (on mug table)
    (manipulable mug)
  )

  (:goal
    (located mug living_room)
  )
)