package satori.metadata;

import java.io.IOException;
import java.io.StringReader;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

import javax.xml.parsers.DocumentBuilderFactory;
import javax.xml.parsers.ParserConfigurationException;

import org.apache.commons.io.LineIterator;
import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.NodeList;
import org.xml.sax.InputSource;
import org.xml.sax.SAXException;

import satori.common.SException;
import satori.common.SPair;
import satori.type.SBlobType;
import satori.type.SSizeType;
import satori.type.STextType;
import satori.type.STimeType;
import satori.type.SType;

public class SParametersParser {
	@SuppressWarnings("serial")
	public static class ParseException extends SException {
		ParseException(String msg) { super(msg); }
		ParseException(Exception ex) { super(ex); }
	}
	
	private static SInputMetadata parseParam(Element node) throws ParseException {
		String type_str = node.getAttribute("type");
		if (type_str.isEmpty()) throw new ParseException("Parameter type undefined");
		SType type;
		if (type_str.equals("text")) type = STextType.INSTANCE;
		else if (type_str.equals("time")) type = STimeType.INSTANCE;
		else if (type_str.equals("size")) type = SSizeType.INSTANCE;
		else if (type_str.equals("blob")) type = SBlobType.INSTANCE;
		else throw new ParseException("Unsupported parameter type: " + type_str);
		String name = node.getAttribute("name");
		if (name.isEmpty()) throw new ParseException("Parameter name undefined");
		String desc = node.getAttribute("description");
		if (desc.isEmpty()) throw new ParseException("Parameter description undefined");
		String required = node.getAttribute("required");
		if (required.isEmpty()) throw new ParseException("Parameter required mode undefined");
		if (!required.equals("true") && !required.equals("false")) throw new ParseException("Invalid parameter required mode: " + required); 
		String def_value = node.getAttribute("default");
		if (def_value.isEmpty()) def_value = null;
		if (def_value != null && type == SBlobType.INSTANCE) throw new ParseException("Default value for blob parameters not supported");
		return new SInputMetadata(name, desc, type, required.equals("true"), def_value);
	}
	
	private static List<SInputMetadata> parseGeneral(Element node) throws ParseException {
		List<SInputMetadata> result = new ArrayList<SInputMetadata>();
		NodeList children = node.getElementsByTagName("param");
		for (int i = 0; i < children.getLength(); ++i) result.add(parseParam((Element)children.item(i)));
		return Collections.unmodifiableList(result);
	}
	private static void verifyGeneral(List<SInputMetadata> params) throws ParseException {
		Set<String> names = new HashSet<String>();
		for (SInputMetadata param : params) {
			if (names.contains(param.getName())) throw new ParseException("Duplicate parameter name: " + param.getName());
			names.add(param.getName());
		}
	}
	
	private static void parse(Document doc, SParameters params) throws ParseException {
		doc.normalizeDocument();
		Element node = doc.getDocumentElement();
		NodeList general_children = node.getElementsByTagName("general");
		List<SInputMetadata> general_meta;
		if (general_children.getLength() == 0) general_meta = Collections.emptyList();
		else if (general_children.getLength() == 1) general_meta = parseGeneral((Element)general_children.item(0));
		else throw new ParseException("Too many general parameter groups");
		verifyGeneral(general_meta);
		params.setGeneralParameters(general_meta);
		params.setTestParameters(Collections.<SInputMetadata>emptyList());
	}
	private static void parse(String str, SParameters params) throws ParseException {
		if (str.isEmpty()) {
			params.setGeneralParameters(Collections.<SInputMetadata>emptyList());
			params.setTestParameters(Collections.<SInputMetadata>emptyList());
			return;
		}
		InputSource is = new InputSource();
		is.setCharacterStream(new StringReader(str));
		try { parse(DocumentBuilderFactory.newInstance().newDocumentBuilder().parse(is), params); }
		catch(IOException ex) { throw new ParseException(ex); }
		catch(SAXException ex) { throw new ParseException(ex); }
		catch(ParserConfigurationException ex) { throw new ParseException(ex); }
	}
	private static void parseLines(String str, SParameters params) throws ParseException {
		StringBuilder xml = new StringBuilder();
		LineIterator line_iter = new LineIterator(new StringReader(str));
		while (line_iter.hasNext()) {
			String line = line_iter.next();
			if (line.startsWith("#@")) xml.append(line.substring(2));
		}
		line_iter.close();
		parse(xml.toString(), params);
	}
	
	private static Map<SPair<String, String>, SParameters> params = new HashMap<SPair<String, String>, SParameters>();
	
	public static SParameters parseParameters(String name, String str) throws ParseException {
		SPair<String, String> key = new SPair<String, String>(name, str);
		if (params.containsKey(key)) return params.get(key);
		SParameters result = new SParameters();
		result.setName(name);
		parseLines(str, result);
		params.put(key, result);
		return result;
	}
}
