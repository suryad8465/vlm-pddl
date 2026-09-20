(define (domain household)

  (:requirements
    :strips
    :typing
    :negative-preconditions
  )

  (:types
    location
    object
  )

  (:predicates

    ;; Robot is currently at a location
    (robot-at ?l - location)

    ;; Two locations can be travelled between
    (connected ?from - location ?to - location)

    ;; An object is located at a location
    (located ?o - object ?l - location)

    ;; An object is on another object/surface
    (on ?o - object ?s - object)

    ;; Robot is currently holding an object
    (holding ?o - object)

    ;; Object can be picked up
    (manipulable ?o - object)
  )


  ;; ==========================================================
  ;; MOVE
  ;; ==========================================================

  (:action move

    :parameters
      (?from - location
       ?to - location)

    :precondition
      (and
        (robot-at ?from)
        (connected ?from ?to)
      )

    :effect
      (and
        (not (robot-at ?from))
        (robot-at ?to)
      )
  )


  ;; ==========================================================
  ;; PICKUP
  ;; ==========================================================

  (:action pickup

    :parameters
      (?o - object
       ?s - object
       ?l - location)

    :precondition
      (and
        (robot-at ?l)
        (located ?o ?l)
        (on ?o ?s)
        (manipulable ?o)
        (not (holding ?o))
      )

    :effect
      (and
        (holding ?o)
        (not (on ?o ?s))
      )
  )


  ;; ==========================================================
  ;; PUTDOWN
  ;; ==========================================================

  (:action putdown

    :parameters
      (?o - object
       ?s - object
       ?l - location)

    :precondition
      (and
        (robot-at ?l)
        (holding ?o)
        (located ?s ?l)
      )

    :effect
      (and
        (on ?o ?s)
        (located ?o ?l)
        (not (holding ?o))
      )
  )
  
  (:action place-at-location
    :parameters
      (?o - object
       ?l - location)
    :precondition
      (and
        (robot-at ?l)
        (holding ?o)
      )
    :effect
      (and
        (located ?o ?l)
        (not (holding ?o))
      )
  )


)
