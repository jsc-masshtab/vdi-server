/* tslint:disable:no-unused-variable */
import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { SpiceComponent } from './spice.component';

describe('SpiceComponent', () => {
  let component: SpiceComponent;
  let fixture: ComponentFixture<SpiceComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ SpiceComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(SpiceComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
