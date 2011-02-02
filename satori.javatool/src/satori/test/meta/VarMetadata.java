package satori.test.meta;

public abstract class VarMetadata extends Metadata {
	private final String name;
	private final String description;

	public String getName() { return name; }
	public String getDescription() { return description; }
	
	public VarMetadata(String name, String description) {
		this.name = name;
		this.description = description;
	}
}
