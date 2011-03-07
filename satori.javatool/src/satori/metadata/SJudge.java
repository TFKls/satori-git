package satori.metadata;

import java.util.List;

import satori.blob.SBlob;

public class SJudge {
	private SBlob blob;
	private String name;
	private List<SInputMetadata> input_meta;
	private List<SOutputMetadata> output_meta;
	
	public SBlob getBlob() { return blob; }
	public String getName() { return name; }
	public List<SInputMetadata> getInputMetadata() { return input_meta; }
	public List<SOutputMetadata> getOutputMetadata() { return output_meta; }
	
	void setBlob(SBlob blob) { this.blob = blob; }
	void setName(String name) { this.name = name; }
	void setInputMetadata(List<SInputMetadata> input_meta) { this.input_meta = input_meta; }
	void setOutputMetadata(List<SOutputMetadata> output_meta) { this.output_meta = output_meta; }
	
	@Override public boolean equals(Object other) {
		if (!(other instanceof SJudge)) return false;
		return blob.equals(((SJudge)other).blob);
	}
	@Override public int hashCode() { return blob.hashCode(); }
}
