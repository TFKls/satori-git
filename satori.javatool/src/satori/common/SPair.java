package satori.common;

public class SPair<T1, T2> {
	public final T1 first;
	public final T2 second;
	
	public SPair(T1 first, T2 second) {
		this.first = first;
		this.second = second;
	}
	
	private boolean equalsAux(SPair<?, ?> other) {
		return first.equals(other.first) && second.equals(other.second);
	}
	@Override public boolean equals(Object other) {
		if (!(other instanceof SPair<?, ?>)) return false;
		return equalsAux((SPair<?, ?>)other);
	}
	@Override public int hashCode() {
		return first.hashCode() ^ second.hashCode();
	}
}
