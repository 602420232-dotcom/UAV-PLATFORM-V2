package com.uav.common.exception;

public class DataNotFoundException extends RuntimeException {
    private final String entity;
    private final Object id;

    public DataNotFoundException(String entity, Object id) {
        super(String.format("%s not found with id: %s", entity, id));
        this.entity = entity;
        this.id = id;
    }

    public DataNotFoundException(String entity, Object id, Throwable cause) {
        super(String.format("%s not found with id: %s", entity, id), cause);
        this.entity = entity;
        this.id = id;
    }

    public String getEntity() {
        return entity;
    }

    public Object getId() {
        return id;
    }
}
