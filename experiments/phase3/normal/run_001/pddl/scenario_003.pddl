(define (problem head_into_cooking_area)
  (:domain household)

  (:objects
    kitchen living_room - location
    table mug kettle - object
  )

  (:init
    (robot-at living_room)
    (connected living_room kitchen)
    (connected kitchen living_room)

    (located table kitchen)
    (located kettle kitchen)
    (located mug kitchen)

    (on kettle table)
    (on mug table)

    (manipulable kettle)
    (manipulable mug)
  )

  (:goal
    (robot-at kitchen)
  )
)