package satori.test.impl;

import satori.test.meta.InputMetadata;

public abstract class Input {
	public abstract InputMetadata getMetadata();
	public abstract void update();
}
