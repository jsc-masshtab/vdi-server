import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { TableIntoComponent } from './table-into';

describe('TableComponentComponent', () => {
  let component: TableIntoComponent;
  let fixture: ComponentFixture<TableIntoComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ TableIntoComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(TableIntoComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
