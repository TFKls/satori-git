package satori.metadata;

import java.util.List;

public class SParametersMetadata {
	private String name;
	private List<SInputMetadata> general_params;
	private List<SInputMetadata> test_params;
	
	public String getName() { return name; }
	public List<SInputMetadata> getGeneralParameters() { return general_params; }
	public List<SInputMetadata> getTestParameters() { return test_params; }
	
	void setName(String name) { this.name = name; }
	void setGeneralParameters(List<SInputMetadata> general_params) { this.general_params = general_params; }
	void setTestParameters(List<SInputMetadata> test_params) { this.test_params = test_params; }
}
